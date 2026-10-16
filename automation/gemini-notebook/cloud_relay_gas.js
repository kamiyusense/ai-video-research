/**
 * AI技術研究室 | Gemini Notebook -> Private GitHub Direct Cloud Bridge (Google Apps Script v0.4)
 *
 * アーキテクチャ (v0.4 GASダイレクト検証・Git Database API単一アトミック保存方式):
 *   GitHub Actions (`repository_dispatch` / `on: push`) を介さず、Google Apps Script (GAS) 単体で:
 *     1. Google Drive Inbox フォルダ内の未処理 Receipt (Google Docs / .json / .md / .txt) を検知
 *     2. `receipt_to_research.py` (v0.4) と100%同一の共通契約 (`contract_spec_v1.json`) に基づき、
 *        スキーマ検証・禁止キー拒否（字幕全文・機密情報の混入防止）・正規化SHA-256計算を実行
 *     3. GitHub REST API (Branches + Git Trees API) とブランチCommit SHAキャッシュを用い、
 *        実行時間制限（6分）に余裕をもって全ブランチ横断の重複検査（registry.json + ファイル名 + 未走査本文）を実行
 *     4. Git Database API (`POST /git/blobs` -> `POST /git/trees` -> `POST /git/commits` ->
 *        `PATCH /git/refs/heads/<branch>` with `force: false`) により、検証合格データのみを
 *        非defaultブランチへ **1回の単一アトミックコミット** で直接保存（`main` は一切変更しない）
 *     5. 直後に Remote Readback（Commit SHA および全ファイルの Git Blob SHA 一致確認）を実施
 *     6. GitHub保存成功後に Google Drive 側の知識索引ドキュメント更新が失敗しても、
 *        `pendingDriveSync` / `lastGitHubCommitSha` vs `lastDriveSyncedCommitSha` の2フェーズ状態管理と
 *        GitHub正本 (`loop_state.json`) からの自己修復 (Self-Healing Reconciliation) により、
 *        次回実行時に重複コミットなしで Drive 側のみを安全に復旧する。
 *
 * 認証キー (Fine-grained PAT) の権限境界に関する重要な区別 (懸念C対策):
 *   - GitHub の Fine-grained PAT (`Contents: Read and Write`) はリポジトリ単位で付与されるため、
 *     トークン自体の仕様だけでは特定のブランチのみに書込みを制限できない場合がある。
 *   - 本スクリプトは【アプリケーション層ガード】として `FORBIDDEN_BRANCHES = ["main", "master"]` と
 *     Ref プレフィックス検査を強制し、`main` へのリクエスト生成自体を拒否する。
 *   - これとは別に【GitHubサーバー層ガード】として、GitHub 側の Branch Protection / Ruleset の状態を
 *     API で確認し、`main_branch_server_protected` として証拠レポートに明記する。
 */

const CONTRACT_SPEC_V1 = {
  contract_version: "gemini_notebook_bridge_contract_v1_4",
  receipt_schema_version: "research_receipt_v1",
  loop_state_schema_version: "gemini_notebook_loop_state_v1",
  expected_repo: "kamiyusense/ai-video-research",
  expected_repo_owner: "kamiyusense",
  expected_repo_name: "ai-video-research",
  default_target_branch: "feature/gemini-notebook-research-loop-20261016",
  forbidden_branches: ["main", "master"],
  default_notebook_url: "https://gemini.google.com/notebook/e87a1d89-15b8-49cf-9adc-bbe7a7fc91c7",
  notebook_internal_master_index_name: "AI技術研究室_知識索引.md",
  github_index_export_file: "automation/gemini-notebook/state/github_knowledge_index_export.md",
  loop_state_file: "automation/gemini-notebook/state/loop_state.json",
  youtube_hosts: ["www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"],
  allowed_statuses: [
    "CONFIRMED_DOC",
    "REPORTED_BY_AUTHOR",
    "CONFIRMED_TEST",
    "UNKNOWN",
    "CONTRADICTED",
  ],
  allowed_changes: ["KNOWN", "NEW", "UPDATED", "CONFLICT", "UNKNOWN"],
  allowed_readback: ["PASS", "FAIL", "UNKNOWN"],
  allowed_dedup_status: ["PASS", "UNKNOWN"],
  forbidden_payload_keys: [
    "transcript",
    "full_transcript",
    "raw_transcript",
    "subtitles",
    "captions",
    "full_text",
    "video_binary",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "private_key",
    "secret",
    "password",
    "authorization",
  ],
  limits: {
    max_videos_per_receipt: 20,
    max_claims_per_video: 12,
    max_title_length: 250,
    max_summary_ja_length: 300,
    max_source_scope_length: 180,
    max_claim_text_length: 500,
    max_next_topics_count: 10,
    max_next_topic_length: 300,
    max_unknowns_count: 20,
    max_unknown_length: 500,
    max_next_topics_queue: 15,
    max_open_unknowns_queue: 25,
    max_blob_fetches_per_run: 25,
  },
  unresolved_backlog_defaults: [
    {
      id: "P006-U01",
      title: "Google AI Studioの長尺YouTube動画入力でのブラウザUIフリーズ回避・映像フレーム直接検証の省力化",
      source: "proposals/006-unresolved-task-backlog-revisit.md",
      status: "OPEN",
    },
    {
      id: "P006-U02",
      title: "Gemini Notebookと非公開GitHub間の手動コピーを最小化する安全な公式連携・差分同期",
      source: "automation/gemini-notebook/README.md",
      status: "IN_PROGRESS",
    },
    {
      id: "P006-U03",
      title: "反復的な画面操作（Computer Use）から公式API・決定的スクリプトへの安全な移行判断",
      source: "research/2026-10-10-lC5jxpYmatE-ai-techniques.md",
      status: "OPEN",
    },
  ],
};

const VIDEO_ID_RE = /^[A-Za-z0-9_-]{11}$/;
const FILENAME_VID_RE = /(?:^|\/)\d{4}-\d{2}-\d{2}-([A-Za-z0-9_-]{11})-[^/]+\.md$/;
const BODY_VID_PATTERNS = [
  /^\s*-\s*video_id:\s*`?([A-Za-z0-9_-]{11})`?\s*$/gm,
  /^\s*-\s*record_id:\s*`?youtube:([A-Za-z0-9_-]{11})`?\s*$/gm,
  /^###\s+\d+[｜|]([A-Za-z0-9_-]{11})\s*$/gm,
  /^\s*-\s*`([A-Za-z0-9_-]{11})`:\s+/gm,
];

function clean_(s) {
  return String(s == null ? "" : s)
    .replace(/\n/g, " ")
    .replace(/\r/g, " ")
    .trim();
}

function validUrl_(value) {
  if (typeof value !== "string" || !value.trim()) return false;
  const m = value.match(/^https:\/\/([^/\s?#]+)(\/[^\s]*)?$/i);
  return Boolean(m && m[1]);
}

function parseUrlParts_(url) {
  if (!validUrl_(url)) return null;
  const m = url.match(/^https:\/\/([^/?#]+)([^?#]*)(\?[^#]*)?(#.*)?$/i);
  if (!m) return null;
  const hostname = m[1].toLowerCase();
  const path = m[2] || "/";
  const queryStr = m[3] ? m[3].slice(1) : "";
  const query = {};
  if (queryStr) {
    queryStr.split("&").forEach(function (pair) {
      const idx = pair.indexOf("=");
      if (idx === -1) {
        query[decodeURIComponent(pair)] = "";
      } else {
        const k = decodeURIComponent(pair.slice(0, idx));
        const v = decodeURIComponent(pair.slice(idx + 1));
        if (query[k] === undefined) query[k] = v;
      }
    });
  }
  return { hostname: hostname, path: path, query: query };
}

function extractYoutubeId_(url) {
  const u = parseUrlParts_(url);
  if (!u) return null;
  if (CONTRACT_SPEC_V1.youtube_hosts.indexOf(u.hostname) === -1) return null;
  let cand = null;
  const parts = u.path.split("/").filter(Boolean);
  if (u.hostname === "youtu.be") {
    cand = parts.length > 0 ? parts[0] : null;
  } else if (u.path === "/watch") {
    cand = u.query.v || null;
  } else if (
    parts.length >= 2 &&
    ["shorts", "live", "embed", "v"].indexOf(parts[0]) !== -1
  ) {
    cand = parts[1];
  }
  if (cand && VIDEO_ID_RE.test(cand)) return cand;
  return null;
}

function canonicalYoutubeUrl_(videoId) {
  return "https://www.youtube.com/watch?v=" + videoId;
}

function extractReceiptFromText_(rawText) {
  if (typeof rawText !== "string" || !rawText.trim()) {
    throw new Error("Empty receipt input");
  }
  const stripped = rawText.trim();
  if (stripped.startsWith("{")) {
    try {
      const data = JSON.parse(stripped);
      if (
        data &&
        typeof data === "object" &&
        !Array.isArray(data) &&
        data.schema_version === CONTRACT_SPEC_V1.receipt_schema_version
      ) {
        return data;
      }
    } catch (e) {}
  }
  const fenceRegex = /```(?:json)?\s*(\{[\s\S]*?\})\s*```/gi;
  let match;
  while ((match = fenceRegex.exec(rawText)) !== null) {
    try {
      const data = JSON.parse(match[1].trim());
      if (
        data &&
        typeof data === "object" &&
        !Array.isArray(data) &&
        data.schema_version === CONTRACT_SPEC_V1.receipt_schema_version
      ) {
        return data;
      }
    } catch (e) {}
  }
  const idx = rawText.indexOf('"research_receipt_v1"');
  if (idx !== -1) {
    let start = rawText.lastIndexOf("{", idx);
    while (start !== -1) {
      let depth = 0;
      let inStr = false;
      let escape = false;
      for (let pos = start; pos < rawText.length; pos++) {
        const ch = rawText[pos];
        if (inStr) {
          if (escape) {
            escape = false;
          } else if (ch === "\\") {
            escape = true;
          } else if (ch === '"') {
            inStr = false;
          }
        } else {
          if (ch === '"') {
            inStr = true;
          } else if (ch === "{") {
            depth += 1;
          } else if (ch === "}") {
            depth -= 1;
            if (depth === 0) {
              const candidate = rawText.slice(start, pos + 1);
              try {
                const data = JSON.parse(candidate);
                if (
                  data &&
                  typeof data === "object" &&
                  !Array.isArray(data) &&
                  data.schema_version === CONTRACT_SPEC_V1.receipt_schema_version
                ) {
                  return data;
                }
              } catch (e) {}
              break;
            }
          }
        }
      }
      start = start > 0 ? rawText.lastIndexOf("{", start - 1) : -1;
    }
  }
  return JSON.parse(stripped);
}

function canonicalizeJson_(val) {
  if (val === null || typeof val !== "object") {
    return JSON.stringify(val);
  }
  if (Array.isArray(val)) {
    return "[" + val.map(canonicalizeJson_).join(",") + "]";
  }
  const keys = Object.keys(val).sort();
  const parts = keys.map(function (k) {
    return JSON.stringify(k) + ":" + canonicalizeJson_(val[k]);
  });
  return "{" + parts.join(",") + "}";
}

function computeCanonicalSha256_(obj) {
  const canonicalJson = canonicalizeJson_(obj);
  if (typeof Utilities !== "undefined" && Utilities.computeDigest) {
    const digestBytes = Utilities.computeDigest(
      Utilities.DigestAlgorithm.SHA_256,
      canonicalJson,
      Utilities.Charset.UTF_8
    );
    return digestBytes
      .map(function (b) {
        return ("0" + (b & 0xff).toString(16)).slice(-2);
      })
      .join("");
  }
  // Node.js fallback for automated cross-language parity verification
  const crypto = require("crypto");
  return crypto.createHash("sha256").update(canonicalJson, "utf8").digest("hex");
}

function scanForbiddenKeys_(val, path) {
  const curPath = path || "root";
  if (!val || typeof val !== "object") return;
  if (Array.isArray(val)) {
    for (let i = 0; i < val.length; i++) {
      scanForbiddenKeys_(val[i], curPath + "[" + i + "]");
    }
    return;
  }
  const forbiddenSet = CONTRACT_SPEC_V1.forbidden_payload_keys;
  const keys = Object.keys(val);
  for (let i = 0; i < keys.length; i++) {
    const k = keys[i];
    const kLower = String(k).trim().toLowerCase();
    if (forbiddenSet.indexOf(kLower) !== -1) {
      throw new Error("Forbidden key in receipt payload: " + curPath + "." + k);
    }
    scanForbiddenKeys_(val[k], curPath + "." + k);
  }
}

function isValidIsoDate_(dateStr) {
  if (typeof dateStr !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
    return false;
  }
  const parts = dateStr.split("-").map(Number);
  const dt = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
  return (
    dt.getUTCFullYear() === parts[0] &&
    dt.getUTCMonth() === parts[1] - 1 &&
    dt.getUTCDate() === parts[2]
  );
}

function validateReceipt_(data) {
  if (
    !data ||
    typeof data !== "object" ||
    Array.isArray(data) ||
    data.schema_version !== CONTRACT_SPEC_V1.receipt_schema_version
  ) {
    throw new Error("Invalid receipt schema_version");
  }
  scanForbiddenKeys_(data, "root");
  if (!validUrl_(data.notebook_url)) {
    throw new Error("Missing/invalid notebook_url");
  }
  if (!isValidIsoDate_(String(data.checked_at || ""))) {
    throw new Error("Invalid checked_at");
  }
  if (CONTRACT_SPEC_V1.allowed_readback.indexOf(data.notebook_readback) === -1) {
    throw new Error("Invalid notebook_readback");
  }
  if (
    data.github_dedup_status !== undefined &&
    data.github_dedup_status !== null &&
    CONTRACT_SPEC_V1.allowed_dedup_status.indexOf(data.github_dedup_status) === -1
  ) {
    throw new Error("Invalid github_dedup_status");
  }
  const lim = CONTRACT_SPEC_V1.limits;
  if (data.next_topics !== undefined && data.next_topics !== null) {
    if (
      !Array.isArray(data.next_topics) ||
      data.next_topics.length > lim.max_next_topics_count ||
      !data.next_topics.every(function (t) {
        return (
          typeof t === "string" &&
          t.trim().length >= 1 &&
          t.trim().length <= lim.max_next_topic_length
        );
      })
    ) {
      throw new Error("Invalid next_topics");
    }
  }
  if (data.unknowns !== undefined && data.unknowns !== null) {
    if (
      !Array.isArray(data.unknowns) ||
      data.unknowns.length > lim.max_unknowns_count ||
      !data.unknowns.every(function (u) {
        return (
          typeof u === "string" &&
          u.trim().length >= 1 &&
          u.trim().length <= lim.max_unknown_length
        );
      })
    ) {
      throw new Error("Invalid unknowns");
    }
  }
  const videos = data.videos;
  if (!Array.isArray(videos) || videos.length > lim.max_videos_per_receipt) {
    throw new Error("videos must be a list of <=20 items");
  }
  const seenIds = {};
  for (let i = 0; i < videos.length; i++) {
    const v = videos[i];
    const vid = v && typeof v === "object" ? v.video_id : null;
    if (typeof vid !== "string" || !VIDEO_ID_RE.test(vid) || seenIds[vid]) {
      throw new Error("Invalid or duplicate video_id");
    }
    seenIds[vid] = true;
    const urlParts = parseUrlParts_(v.url);
    if (
      !urlParts ||
      CONTRACT_SPEC_V1.youtube_hosts.indexOf(urlParts.hostname) === -1
    ) {
      throw new Error("Video URL must be YouTube HTTPS");
    }
    const extractedId = extractYoutubeId_(v.url);
    if (extractedId !== null && extractedId !== vid) {
      throw new Error(
        "Video URL ID (" + extractedId + ") does not match video_id (" + vid + ")"
      );
    }
    if (
      typeof v.title !== "string" ||
      v.title.length < 1 ||
      v.title.length > lim.max_title_length
    ) {
      throw new Error("Invalid title");
    }
    if (
      typeof v.summary_ja !== "string" ||
      v.summary_ja.length < 1 ||
      v.summary_ja.length > lim.max_summary_ja_length
    ) {
      throw new Error("Summary must contain 1-300 characters");
    }
    if (
      typeof v.source_scope !== "string" ||
      v.source_scope.length > lim.max_source_scope_length
    ) {
      throw new Error("Invalid source_scope");
    }
    if (CONTRACT_SPEC_V1.allowed_readback.indexOf(v.notebook_readback) === -1) {
      throw new Error("Invalid notebook source readback");
    }
    if (
      !Array.isArray(v.changes) ||
      v.changes.length === 0 ||
      !v.changes.every(function (ch) {
        return CONTRACT_SPEC_V1.allowed_changes.indexOf(ch) !== -1;
      })
    ) {
      throw new Error("Invalid changes");
    }
    const claims = v.claims;
    if (!Array.isArray(claims) || claims.length > lim.max_claims_per_video) {
      throw new Error("Claims must be a list of <=12 items");
    }
    for (let j = 0; j < claims.length; j++) {
      const c = claims[j];
      if (
        !c ||
        typeof c !== "object" ||
        typeof c.text !== "string" ||
        c.text.length > lim.max_claim_text_length
      ) {
        throw new Error("Invalid claim");
      }
      if (CONTRACT_SPEC_V1.allowed_statuses.indexOf(c.status) === -1) {
        throw new Error("Invalid claim status");
      }
      const t = c.timestamp_seconds;
      if (
        t !== undefined &&
        t !== null &&
        (typeof t !== "number" || !Number.isInteger(t) || typeof t === "boolean" || t < 0)
      ) {
        throw new Error("Invalid timestamp");
      }
      const u = c.official_url;
      if (u !== undefined && u !== null && !validUrl_(u)) {
        throw new Error("Invalid official_url");
      }
    }
  }
  return videos;
}

function pad2_(n) {
  const s = String(Math.floor(n));
  return s.length < 2 ? "0" + s : s;
}

function formatClaimsLines_(vid, claims) {
  const lines = [];
  for (let i = 0; i < claims.length; i++) {
    const c = claims[i];
    const t = c.timestamp_seconds;
    let timeRef = "UNKNOWN";
    if (t !== undefined && t !== null) {
      const mins = Math.floor(t / 60);
      const secs = t % 60;
      timeRef =
        "[" +
        pad2_(mins) +
        ":" +
        pad2_(secs) +
        "](https://www.youtube.com/watch?v=" +
        vid +
        "&t=" +
        t +
        "s)";
    }
    lines.push(
      "- " +
        clean_(c.text) +
        " | " +
        c.status +
        " | time: " +
        timeRef +
        " | official: " +
        (c.official_url || "UNKNOWN")
    );
  }
  return lines;
}

function renderResearchMarkdown_(v, checkedAt) {
  const vid = v.video_id;
  const canon = canonicalYoutubeUrl_(vid);
  let lines = [
    "# " + clean_(v.title),
    "",
    "- record_id: `youtube:" + vid + "`",
    "- video_id: `" + vid + "`",
    "- canonical_url: " + canon,
    "- original_url: " + v.url,
    "- publication_date: " + clean_(v.published_at || "UNKNOWN"),
    "- checked_at: " + checkedAt,
    "- source_scope: " + clean_(v.source_scope),
    "- Gemini Notebook source: " + clean_(v.notebook_source_id || "UNKNOWN"),
    "- Gemini readback (self-reported): " + v.notebook_readback,
    "- GitHub independent verification: NOT_RUN",
    "- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB",
    "- changes: " + v.changes.join(", "),
    "",
    "## 独自要約",
    clean_(v.summary_ja),
    "",
    "## 主張・一次資料・時刻",
  ];
  lines = lines.concat(formatClaimsLines_(vid, v.claims));
  lines = lines.concat([
    "",
    "## 限界",
    "Gemini報告を基にした研究候補。映像実見・GitHub側の独立照合は別。またGitHubへの保存はNotebook内の総合索引更新を意味しない。",
    "",
  ]);
  return lines.join("\n");
}

function renderDeltaSection_(v, checkedAt) {
  const vid = v.video_id;
  const changesStr = v.changes.join(", ");
  let lines = [
    "",
    "## 差分更新 (" + checkedAt + " / " + changesStr + ")",
    "",
    "- checked_at: " + checkedAt,
    "- source_scope: " + clean_(v.source_scope),
    "- Gemini Notebook source: " + clean_(v.notebook_source_id || "UNKNOWN"),
    "- Gemini readback (self-reported): " + v.notebook_readback,
    "- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB",
    "- changes: " + changesStr,
    "",
    "### 差分要約",
    clean_(v.summary_ja),
    "",
    "### 追加・更新された主張と検証",
  ];
  lines = lines.concat(formatClaimsLines_(vid, v.claims));
  lines.push("");
  return lines.join("\n");
}

function extractVideoIdsFromMarkdownText_(mdText) {
  const found = [];
  const seen = {};
  if (typeof mdText !== "string") return found;
  for (let i = 0; i < BODY_VID_PATTERNS.length; i++) {
    const regex = new RegExp(BODY_VID_PATTERNS[i].source, "gm");
    let m;
    while ((m = regex.exec(mdText)) !== null) {
      const vid = m[1];
      if (VIDEO_ID_RE.test(vid) && !seen[vid]) {
        seen[vid] = true;
        found.push(vid);
      }
    }
  }
  return found;
}

function defaultInitialLoopState_() {
  return {
    schema_version: CONTRACT_SPEC_V1.loop_state_schema_version,
    repository: CONTRACT_SPEC_V1.expected_repo,
    notebook_url: CONTRACT_SPEC_V1.default_notebook_url,
    notebook_internal_master_index_name: CONTRACT_SPEC_V1.notebook_internal_master_index_name,
    github_index_export_file: CONTRACT_SPEC_V1.github_index_export_file,
    notebook_sync_status: "NOT_SYNCED_FROM_GITHUB",
    last_updated: null,
    processed_receipts: [],
    next_topics_queue: [],
    open_unknowns: [],
    unresolved_backlog_refs: JSON.parse(
      JSON.stringify(CONTRACT_SPEC_V1.unresolved_backlog_defaults)
    ),
  };
}

function validateLoopStateSchema_(state, statePathLabel) {
  const label = statePathLabel || CONTRACT_SPEC_V1.loop_state_file;
  if (!state || typeof state !== "object" || Array.isArray(state)) {
    throw new Error(
      "Corrupted loop_state.json at " +
        label +
        ": root must be a JSON object (refusing to reset existing state)"
    );
  }
  if (state.schema_version !== CONTRACT_SPEC_V1.loop_state_schema_version) {
    throw new Error(
      "Corrupted loop_state.json at " +
        label +
        ": unexpected schema_version=" +
        JSON.stringify(state.schema_version) +
        " (refusing to reset existing state)"
    );
  }
  const listKeys = ["processed_receipts", "next_topics_queue", "open_unknowns"];
  for (let i = 0; i < listKeys.length; i++) {
    const k = listKeys[i];
    if (!Array.isArray(state[k])) {
      throw new Error(
        "Corrupted loop_state.json at " +
          label +
          ": '" +
          k +
          "' must be a list (refusing to reset existing state)"
      );
    }
  }
  return state;
}

function renderGitHubKnowledgeIndexExportMd_(
  registry,
  localMap,
  remoteMap,
  loopState,
  freshness
) {
  const regRecords = {};
  const recordsList = (registry && registry.records) || [];
  for (let i = 0; i < recordsList.length; i++) {
    const r = recordsList[i];
    if (r && typeof r === "object" && r.video_id) {
      regRecords[r.video_id] = r;
    }
  }
  const allVidsSet = {};
  Object.keys(regRecords).forEach(function (k) {
    allVidsSet[k] = true;
  });
  Object.keys(localMap || {}).forEach(function (k) {
    allVidsSet[k] = true;
  });
  Object.keys(remoteMap || {}).forEach(function (k) {
    allVidsSet[k] = true;
  });
  const allVids = Object.keys(allVidsSet).sort();

  const expectedRepo = CONTRACT_SPEC_V1.expected_repo;
  const masterIndexName = CONTRACT_SPEC_V1.notebook_internal_master_index_name;
  const notebookUrl =
    (loopState && loopState.notebook_url) || CONTRACT_SPEC_V1.default_notebook_url;
  const lastUpdated = (loopState && loopState.last_updated) || "INITIAL";
  const syncStatus =
    (loopState && loopState.notebook_sync_status) || "NOT_SYNCED_FROM_GITHUB";

  let lines = [
    "# GitHub正本 知識索引・差分エクスポート (`github_knowledge_index_export.md`)",
    "",
    "> **【重要：索引の区別と上書き禁止】**",
    "> - このファイルは **GitHub 正本（`" +
      expectedRepo +
      "`）側の既知動画台帳・未解決課題・次回テーマの差分エクスポート** です。",
    "> - Gemini Notebook 内に既存の総合索引ソース **`" +
      masterIndexName +
      "`**（先行16ソース等の蓄積を含む総合索引）とは**別物**です。",
    "> - Notebook 内の `" +
      masterIndexName +
      "` をこのファイルで丸ごと上書き置換しないでください。Notebook 側では既存内容を維持したまま差分追記（または別ソースとして参照）してください。",
    "> - **GitHub への保存成功は、Gemini Notebook への同期完了を意味しません** (`notebook_sync_status: NOT_SYNCED_FROM_GITHUB`)。",
    "",
    "- 対象リポジトリ: `" + expectedRepo + "` (private)",
    "- 補助知識庫 (Gemini Notebook): " + notebookUrl,
    "- GitHub側エクスポート更新日: " + lastUpdated,
    "- リモートブランチ照合鮮度: `" + freshness + "`",
    "- Notebook側への逆同期状態: `" + syncStatus + "`",
    "",
    "## 1. GitHub全ブランチ横断・既知の動画ID台帳（重複登録禁止リスト）",
    "",
    "`registry.json` だけでなく、`research/*.md` および `notes/*.md` のファイル名・本文から検出された動画IDを含みます。",
    "",
    "| video_id | 状態 | 検出元 (現在ブランチ / 並行PRブランチ) | 参照パス |",
    "|---|---|---|---|",
  ];

  for (let i = 0; i < allVids.length; i++) {
    const vid = allVids[i];
    let status = "";
    let rpath = "";
    let loc = "";
    if (regRecords[vid]) {
      const rec = regRecords[vid];
      status = clean_(rec.status || "RECORDED");
      rpath = clean_(rec.research_path || "");
      loc = "current_branch (registry.json)";
    } else if (localMap && localMap[vid]) {
      const linfo = localMap[vid];
      status = clean_(linfo.status || "LOCAL_MARKDOWN");
      rpath = clean_(linfo.research_path || "");
      loc = "current_branch (" + (linfo.source || "markdown") + ")";
    } else {
      const rinfo = remoteMap[vid];
      status = clean_(rinfo.status || "REMOTE_BRANCH_ONLY");
      rpath = clean_(rinfo.research_path || "");
      const via = rinfo.detected_via || "remote";
      const branches = (rinfo.branches || []).join(", ");
      loc = branches + " (" + via + ")";
    }
    lines.push("| `" + vid + "` | " + status + " | " + loc + " | `" + rpath + "` |");
  }

  lines = lines.concat(["", "## 2. 優先研究テーマ・次回調査キュー (`next_topics`)", ""]);
  const queue = (loopState && loopState.next_topics_queue) || [];
  if (queue.length > 0) {
    for (let i = 0; i < queue.length; i++) {
      lines.push(i + 1 + ". " + clean_(queue[i]));
    }
  } else {
    lines = lines.concat([
      "1. R001/R002: 自律研究Loopの完了条件・停止条件と、重複イベントや結果不明書込みの安全な復旧パターン",
      "2. R004/R005: ハーネス・MCP・プラグイン・公式コネクタの権限境界とモデル非依存の状態管理",
      "3. P006連携: 新しいAI機能・ツール発表時に「過去の未解決課題」と自動照合して再挑戦を提案する仕組み",
    ]);
  }

  lines = lines.concat(["", "## 3. 未確認・要検証事項 (`unknowns`)", ""]);
  const unknowns = (loopState && loopState.open_unknowns) || [];
  if (unknowns.length > 0) {
    for (let i = 0; i < unknowns.length; i++) {
      lines.push("- " + clean_(unknowns[i]));
    }
  } else {
    lines = lines.concat([
      "- Gemini Taskの定期スケジュール実行時におけるNotebookソース追加・索引更新の無人完走可否",
      "- YouTubeソース（文字起こしのみ）では確認できない画面実演・UI操作の軽量な検証手段",
    ]);
  }

  lines = lines.concat([
    "",
    "## 4. 未解決課題ストック（P006 再評価対象）",
    "",
    "新技術・新機能を発見した際は、以下の未解決課題を解決できる一次資料の根拠があるか照合すること：",
    "",
  ]);
  const backlog = (loopState && loopState.unresolved_backlog_refs) || [];
  for (let i = 0; i < backlog.length; i++) {
    const item = backlog[i];
    lines.push(
      "- **" +
        clean_(item.id || "") +
        "**: " +
        clean_(item.title || "") +
        " (状態: `" +
        clean_(item.status || "OPEN") +
        "`, 参照: `" +
        clean_(item.source || "") +
        "`)"
    );
  }
  lines.push("");
  return lines.join("\n");
}

/**
 * GitHub API ヘルパー (retry=0 / muteHttpExceptions=true)
 */
function githubApiRequest_(token, method, endpointPath, payloadObj, acceptHeader, customFetcher) {
  const fetcher = customFetcher || (typeof UrlFetchApp !== "undefined" ? UrlFetchApp : null);
  if (!fetcher) {
    throw new Error("No HTTP fetcher (UrlFetchApp) available");
  }
  const url = "https://api.github.com" + endpointPath;
  const options = {
    method: method.toLowerCase(),
    headers: {
      Authorization: "Bearer " + token,
      Accept: acceptHeader || "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    muteHttpExceptions: true,
  };
  if (payloadObj !== undefined && payloadObj !== null) {
    options.contentType = "application/json";
    options.payload = JSON.stringify(payloadObj);
  }
  const res = fetcher.fetch(url, options);
  const code = res.getResponseCode();
  const text = res.getContentText("UTF-8");
  let json = null;
  if (text && (!acceptHeader || acceptHeader.indexOf("raw") === -1)) {
    try {
      json = JSON.parse(text);
    } catch (e) {}
  }
  return { code: code, text: text, json: json };
}

function decodeGitBlobText_(blobJson) {
  if (!blobJson || typeof blobJson.content !== "string") return "";
  const cleanB64 = blobJson.content.replace(/\s+/g, "");
  if (typeof Utilities !== "undefined" && Utilities.base64Decode) {
    const bytes = Utilities.base64Decode(cleanB64);
    return Utilities.newBlob(bytes).getDataAsString("UTF-8");
  }
  return Buffer.from(cleanB64, "base64").toString("utf8");
}

function verifyTargetBranchBoundary_(targetBranch) {
  const cleanBranch = String(targetBranch || "").trim();
  if (
    !cleanBranch ||
    CONTRACT_SPEC_V1.forbidden_branches.indexOf(cleanBranch) !== -1 ||
    cleanBranch.indexOf("refs/heads/main") !== -1 ||
    cleanBranch.indexOf("refs/heads/master") !== -1
  ) {
    throw new Error(
      "Refusing detached/default-branch write (Application-Level Guard): " + cleanBranch
    );
  }
  return cleanBranch;
}

/**
 * 懸念B対策: Git Trees API とブランチCommit SHAキャッシュを用いた省通信・高速な全ブランチ横断重複照合
 */
function collectGitHubRepositoryState_(token, targetBranch, branchCache, customFetcher) {
  const owner = CONTRACT_SPEC_V1.expected_repo_owner;
  const repo = CONTRACT_SPEC_V1.expected_repo_name;
  const baseRepoPath = "/repos/" + owner + "/" + repo;

  // 1. 全ブランチ一覧と最新Commit SHAを1回のAPI呼出しで取得
  const branchesRes = githubApiRequest_(
    token,
    "get",
    baseRepoPath + "/branches?per_page=100",
    null,
    null,
    customFetcher
  );
  if (branchesRes.code !== 200 || !Array.isArray(branchesRes.json)) {
    throw new Error(
      "Failed to fetch fresh remote branches from GitHub API (HTTP " +
        branchesRes.code +
        "): refusing to trust stale state"
    );
  }

  let mainBranchServerProtected = false;
  let targetBranchCommitSha = null;
  const remoteBranches = [];

  for (let i = 0; i < branchesRes.json.length; i++) {
    const b = branchesRes.json[i];
    if (b.name === "main") {
      mainBranchServerProtected = Boolean(b.protected);
    }
    if (b.name === targetBranch) {
      targetBranchCommitSha = b.commit && b.commit.sha;
    } else if (CONTRACT_SPEC_V1.forbidden_branches.indexOf(b.name) === -1) {
      remoteBranches.push({
        name: b.name,
        ref: "origin/" + b.name,
        commitSha: b.commit && b.commit.sha,
      });
    }
  }

  if (!targetBranchCommitSha) {
    throw new Error("Target branch not found on GitHub: " + targetBranch);
  }

  // 2. TargetブランチのCommit情報（baseTreeSha）とRecursive Treeを1回で取得
  const commitRes = githubApiRequest_(
    token,
    "get",
    baseRepoPath + "/git/commits/" + targetBranchCommitSha,
    null,
    null,
    customFetcher
  );
  if (commitRes.code !== 200 || !commitRes.json || !commitRes.json.tree) {
    throw new Error("Failed to read target branch commit: HTTP " + commitRes.code);
  }
  const baseTreeSha = commitRes.json.tree.sha;

  const targetTreeRes = githubApiRequest_(
    token,
    "get",
    baseRepoPath + "/git/trees/" + baseTreeSha + "?recursive=1",
    null,
    null,
    customFetcher
  );
  if (targetTreeRes.code !== 200 || !targetTreeRes.json || !Array.isArray(targetTreeRes.json.tree)) {
    throw new Error("Failed to read target branch git tree: HTTP " + targetTreeRes.code);
  }

  const targetFilesByPath = {};
  for (let i = 0; i < targetTreeRes.json.tree.length; i++) {
    const item = targetTreeRes.json.tree[i];
    if (item.type === "blob") {
      targetFilesByPath[item.path] = item.sha;
    }
  }

  function fetchBlobTextBySha(blobSha) {
    const bRes = githubApiRequest_(
      token,
      "get",
      baseRepoPath + "/git/blobs/" + blobSha,
      null,
      null,
      customFetcher
    );
    if (bRes.code !== 200 || !bRes.json) {
      throw new Error("Failed to read git blob " + blobSha + ": HTTP " + bRes.code);
    }
    return decodeGitBlobText_(bRes.json);
  }

  // 3. Targetブランチの registry.json と loop_state.json を取得・検証
  if (!targetFilesByPath["registry.json"]) {
    throw new Error("registry.json missing on target branch " + targetBranch);
  }
  const registry = JSON.parse(fetchBlobTextBySha(targetFilesByPath["registry.json"]));
  if (
    registry.repository !== CONTRACT_SPEC_V1.expected_repo ||
    !Array.isArray(registry.records)
  ) {
    throw new Error("Unexpected registry.json on target branch");
  }

  let loopState = null;
  const stateFilePath = CONTRACT_SPEC_V1.loop_state_file;
  if (targetFilesByPath[stateFilePath]) {
    const rawState = fetchBlobTextBySha(targetFilesByPath[stateFilePath]);
    let parsedState;
    try {
      parsedState = JSON.parse(rawState);
    } catch (e) {
      throw new Error(
        "Corrupted JSON in loop_state.json at " +
          stateFilePath +
          ": " +
          e.message +
          " (refusing to reset existing state)"
      );
    }
    loopState = validateLoopStateSchema_(parsedState, stateFilePath);
  } else {
    loopState = defaultInitialLoopState_();
  }

  // 4. Targetブランチ内の localMap と既存 research/*.md 一覧を構築（ファイル名優先＋必要時のみBlob読取）
  const localMap = {};
  const existingResearchMdByVid = {};
  for (let i = 0; i < registry.records.length; i++) {
    const r = registry.records[i];
    if (r && VIDEO_ID_RE.test(String(r.video_id || ""))) {
      localMap[r.video_id] = {
        video_id: r.video_id,
        source: "registry.json",
        research_path: r.research_path || "",
        status: r.status || "RECORDED",
      };
    }
  }

  let blobFetchesUsed = 0;
  const maxBlobFetches = CONTRACT_SPEC_V1.limits.max_blob_fetches_per_run;
  const targetPaths = Object.keys(targetFilesByPath).sort();
  for (let i = 0; i < targetPaths.length; i++) {
    const relPath = targetPaths[i];
    if (
      !(relPath.startsWith("research/") || relPath.startsWith("notes/")) ||
      !relPath.endsWith(".md")
    ) {
      continue;
    }
    const mName = relPath.match(FILENAME_VID_RE);
    if (mName) {
      const vid = mName[1];
      if (relPath.startsWith("research/") && !existingResearchMdByVid[vid]) {
        existingResearchMdByVid[vid] = relPath;
      }
      if (!localMap[vid]) {
        localMap[vid] = {
          video_id: vid,
          source: "filename:" + relPath,
          research_path: relPath,
          status: "RECORDED_IN_RESEARCH_FILE_UNREGISTERED",
        };
      }
    }
    // notes/*.md またはファイル名からIDが取れない research/*.md のみ本文を走査
    if (relPath.startsWith("notes/") || !mName) {
      if (blobFetchesUsed < maxBlobFetches) {
        blobFetchesUsed += 1;
        const body = fetchBlobTextBySha(targetFilesByPath[relPath]);
        const bodyVids = extractVideoIdsFromMarkdownText_(body);
        for (let k = 0; k < bodyVids.length; k++) {
          const bVid = bodyVids[k];
          if (!localMap[bVid]) {
            localMap[bVid] = {
              video_id: bVid,
              source: "body:" + relPath,
              research_path: relPath,
              status: "REFERENCED_IN_RESEARCH_OR_NOTE_BODY",
            };
          }
        }
      }
    }
  }

  // 5. 他ブランチ (origin/*) の増分キャッシュ照合
  const remoteMap = {};
  const cacheObj = branchCache || {};
  remoteBranches.sort(function (a, b) {
    return a.ref < b.ref ? -1 : a.ref > b.ref ? 1 : 0;
  });

  for (let i = 0; i < remoteBranches.length; i++) {
    const rb = remoteBranches[i];
    const cached = cacheObj[rb.ref];
    if (cached && cached.commit_sha === rb.commitSha && Array.isArray(cached.videos)) {
      for (let j = 0; j < cached.videos.length; j++) {
        const entry = cached.videos[j];
        if (!remoteMap[entry.video_id]) {
          remoteMap[entry.video_id] = {
            video_id: entry.video_id,
            canonical_url: entry.canonical_url || canonicalYoutubeUrl_(entry.video_id),
            research_path: entry.research_path || "",
            status: entry.status || "UNKNOWN",
            detected_via: entry.detected_via || "cache",
            branches: [],
          };
        }
        if (remoteMap[rb.ref] === undefined && remoteMap[entry.video_id].branches.indexOf(rb.ref) === -1) {
          remoteMap[entry.video_id].branches.push(rb.ref);
        }
      }
      continue;
    }

    // キャッシュ未ヒット時: そのブランチのGit Treeを1回のAPIで取得
    const rbTreeRes = githubApiRequest_(
      token,
      "get",
      baseRepoPath + "/git/trees/" + rb.commitSha + "?recursive=1",
      null,
      null,
      customFetcher
    );
    if (rbTreeRes.code !== 200 || !rbTreeRes.json || !Array.isArray(rbTreeRes.json.tree)) {
      continue;
    }
    const rbEntries = {};
    const rbBlobs = {};
    for (let j = 0; j < rbTreeRes.json.tree.length; j++) {
      const tItem = rbTreeRes.json.tree[j];
      if (tItem.type === "blob") {
        rbBlobs[tItem.path] = tItem.sha;
      }
    }

    if (rbBlobs["registry.json"]) {
      try {
        const rbReg = JSON.parse(fetchBlobTextBySha(rbBlobs["registry.json"]));
        const recs = rbReg.records || [];
        for (let j = 0; j < recs.length; j++) {
          const rec = recs[j];
          if (rec && VIDEO_ID_RE.test(String(rec.video_id || ""))) {
            const vid = rec.video_id;
            const entry = {
              video_id: vid,
              canonical_url: rec.canonical_url || canonicalYoutubeUrl_(vid),
              research_path: rec.research_path || "",
              status: rec.status || "UNKNOWN",
              detected_via: "registry.json",
            };
            if (!rbEntries[vid]) rbEntries[vid] = entry;
            if (!remoteMap[vid]) {
              remoteMap[vid] = {
                video_id: vid,
                canonical_url: entry.canonical_url,
                research_path: entry.research_path,
                status: entry.status,
                detected_via: entry.detected_via,
                branches: [],
              };
            }
            if (remoteMap[vid].branches.indexOf(rb.ref) === -1) {
              remoteMap[vid].branches.push(rb.ref);
            }
          }
        }
      } catch (e) {}
    }

    const rbPaths = Object.keys(rbBlobs).sort();
    for (let j = 0; j < rbPaths.length; j++) {
      const relPath = rbPaths[j];
      if (
        !(relPath.startsWith("research/") || relPath.startsWith("notes/")) ||
        !relPath.endsWith(".md")
      ) {
        continue;
      }
      const mName = relPath.match(FILENAME_VID_RE);
      if (mName) {
        const vid = mName[1];
        const entry = {
          video_id: vid,
          canonical_url: canonicalYoutubeUrl_(vid),
          research_path: relPath,
          status: "REMOTE_RESEARCH_FILE",
          detected_via: "filename:" + relPath,
        };
        if (!rbEntries[vid]) rbEntries[vid] = entry;
        if (!remoteMap[vid]) {
          remoteMap[vid] = {
            video_id: vid,
            canonical_url: entry.canonical_url,
            research_path: entry.research_path,
            status: entry.status,
            detected_via: entry.detected_via,
            branches: [],
          };
        }
        if (remoteMap[vid].branches.indexOf(rb.ref) === -1) {
          remoteMap[vid].branches.push(rb.ref);
        }
      }
      if ((relPath.startsWith("notes/") || !mName) && blobFetchesUsed < maxBlobFetches) {
        blobFetchesUsed += 1;
        const body = fetchBlobTextBySha(rbBlobs[relPath]);
        const bodyVids = extractVideoIdsFromMarkdownText_(body);
        for (let k = 0; k < bodyVids.length; k++) {
          const bVid = bodyVids[k];
          const entry = {
            video_id: bVid,
            canonical_url: canonicalYoutubeUrl_(bVid),
            research_path: relPath,
            status: "REMOTE_MARKDOWN_REFERENCE",
            detected_via: "body:" + relPath,
          };
          if (!rbEntries[bVid]) rbEntries[bVid] = entry;
          if (!remoteMap[bVid]) {
            remoteMap[bVid] = {
              video_id: bVid,
              canonical_url: entry.canonical_url,
              research_path: entry.research_path,
              status: entry.status,
              detected_via: entry.detected_via,
              branches: [],
            };
          }
          if (remoteMap[bVid].branches.indexOf(rb.ref) === -1) {
            remoteMap[bVid].branches.push(rb.ref);
          }
        }
      }
    }

    cacheObj[rb.ref] = {
      commit_sha: rb.commitSha,
      videos: Object.keys(rbEntries).map(function (k) {
        return rbEntries[k];
      }),
    };
  }

  return {
    targetBranchCommitSha: targetBranchCommitSha,
    baseTreeSha: baseTreeSha,
    targetFilesByPath: targetFilesByPath,
    registry: registry,
    loopState: loopState,
    localMap: localMap,
    existingResearchMdByVid: existingResearchMdByVid,
    remoteMap: remoteMap,
    freshness: "FRESH_FETCHED",
    mainBranchServerProtected: mainBranchServerProtected,
    fetchBlobTextBySha: fetchBlobTextBySha,
    branchCache: cacheObj,
  };
}

/**
 * Receipt 1件を検証し、更新対象ファイル群（インメモリ）を計算する純粋パイプライン
 */
function planReceiptApplication_(data, repoState) {
  const videos = validateReceipt_(data);
  const digest = computeCanonicalSha256_(data);

  const registry = JSON.parse(JSON.stringify(repoState.registry));
  const loopState = JSON.parse(JSON.stringify(repoState.loopState));
  const localMap = JSON.parse(JSON.stringify(repoState.localMap));
  const remoteMap = repoState.remoteMap || {};
  const existingMdMap = repoState.existingResearchMdByVid || {};

  const processedHashes = {};
  (loopState.processed_receipts || []).forEach(function (p) {
    if (p && p.sha256) processedHashes[p.sha256] = true;
  });

  const localRecordsById = {};
  (registry.records || []).forEach(function (r) {
    if (r && r.video_id) localRecordsById[r.video_id] = r;
  });

  const plannedNew = [];
  const plannedUpdates = [];
  const skipped = [];

  if (processedHashes[digest]) {
    for (let i = 0; i < videos.length; i++) {
      skipped.push({ video_id: videos[i].video_id, reason: "SKIP_DUPLICATE_RECEIPT" });
    }
  } else {
    for (let i = 0; i < videos.length; i++) {
      const v = videos[i];
      const vid = v.video_id;
      const existingMdPath = existingMdMap[vid] || null;
      const isLocalKnown = Boolean(
        localRecordsById[vid] || localMap[vid] || existingMdPath
      );
      const isRemoteKnown = Boolean(remoteMap[vid] && !isLocalKnown);
      const hasUpdateFlag =
        v.changes.indexOf("UPDATED") !== -1 || v.changes.indexOf("CONFLICT") !== -1;

      if (v.notebook_readback !== "PASS") {
        skipped.push({ video_id: vid, reason: "SKIP_UNVERIFIED_NOTEBOOK" });
        continue;
      }
      if (v.source_scope.toUpperCase().indexOf("METADATA_ONLY") !== -1) {
        skipped.push({ video_id: vid, reason: "SKIP_METADATA_ONLY" });
        continue;
      }

      if (isLocalKnown) {
        if (hasUpdateFlag && existingMdPath && repoState.fetchBlobTextBySha) {
          const blobSha = repoState.targetFilesByPath[existingMdPath];
          const currentContent = blobSha ? repoState.fetchBlobTextBySha(blobSha) : "";
          const deltaText = renderDeltaSection_(v, data.checked_at);
          if (
            currentContent.indexOf(clean_(v.summary_ja)) !== -1 ||
            currentContent.indexOf("## 差分更新 (" + data.checked_at) !== -1
          ) {
            skipped.push({
              video_id: vid,
              reason: "SKIP_EXISTING_DELTA_ALREADY_APPLIED",
            });
            continue;
          }
          const sep = currentContent.endsWith("\n") ? "" : "\n";
          const newContent =
            currentContent + sep + deltaText.replace(/^\n+/, "");
          plannedUpdates.push({
            path: existingMdPath,
            content: newContent,
            video: v,
          });
        } else {
          const sourceDetail =
            (localMap[vid] && localMap[vid].source) || "local";
          skipped.push({
            video_id: vid,
            reason: "SKIP_EXISTING",
            detected_via: sourceDetail,
          });
        }
        continue;
      }

      if (isRemoteKnown) {
        skipped.push({
          video_id: vid,
          reason: "SKIP_EXISTING_REMOTE_BRANCH",
          branches: remoteMap[vid].branches || [],
          detected_via: remoteMap[vid].detected_via || "remote",
        });
        continue;
      }

      const dstPath =
        "research/" + data.checked_at + "-" + vid + "-gemini-notebook.md";
      if (repoState.targetFilesByPath && repoState.targetFilesByPath[dstPath]) {
        skipped.push({ video_id: vid, reason: "SKIP_EXISTS" });
        continue;
      }
      plannedNew.push({
        path: dstPath,
        content: renderResearchMarkdown_(v, data.checked_at),
        video: v,
      });
    }
  }

  const filesToCommit = {};
  for (let i = 0; i < plannedNew.length; i++) {
    const item = plannedNew[i];
    const v = item.video;
    filesToCommit[item.path] = item.content;
    const recEntry = {
      record_id: "youtube:" + v.video_id,
      video_id: v.video_id,
      canonical_url: canonicalYoutubeUrl_(v.video_id),
      research_path: item.path,
      source_scope: v.source_scope,
      research_date: data.checked_at,
      status:
        "GEMINI_REPORTED; NOTEBOOK_READBACK_REPORTED; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE",
      evidence: "GEMINI_RESEARCH_RECEIPT",
    };
    if (v.url !== recEntry.canonical_url) {
      recEntry.original_url = v.url;
    }
    registry.records.push(recEntry);
    localMap[v.video_id] = {
      video_id: v.video_id,
      source: "registry.json",
      research_path: item.path,
      status: recEntry.status,
    };
  }

  for (let i = 0; i < plannedUpdates.length; i++) {
    const uItem = plannedUpdates[i];
    const v = uItem.video;
    filesToCommit[uItem.path] = uItem.content;
    const rec = localRecordsById[v.video_id];
    if (rec) {
      rec.last_updated = data.checked_at;
      if (!Array.isArray(rec.update_history)) rec.update_history = [];
      rec.update_history.push({
        checked_at: data.checked_at,
        changes: v.changes,
        source_scope: v.source_scope,
      });
    }
  }

  if (plannedNew.length > 0 || plannedUpdates.length > 0) {
    filesToCommit["registry.json"] = JSON.stringify(registry, null, 2) + "\n";
  }

  // loop_state.json と github_knowledge_index_export.md の更新
  loopState.last_updated = data.checked_at;
  loopState.notebook_internal_master_index_name =
    CONTRACT_SPEC_V1.notebook_internal_master_index_name;
  loopState.github_index_export_file = CONTRACT_SPEC_V1.github_index_export_file;
  loopState.notebook_sync_status = "NOT_SYNCED_FROM_GITHUB";
  if (data.notebook_url) {
    loopState.notebook_url = data.notebook_url;
  }

  const alreadyRecordedInState = Boolean(processedHashes[digest]);
  if (!alreadyRecordedInState && (plannedNew.length > 0 || plannedUpdates.length > 0)) {
    loopState.processed_receipts.push({
      sha256: digest,
      checked_at: data.checked_at,
      new_video_ids: plannedNew.map(function (x) {
        return x.video.video_id;
      }),
      updated_video_ids: plannedUpdates.map(function (x) {
        return x.video.video_id;
      }),
      github_write_status: "APPLIED_ATOMIC_COMMIT",
      notebook_sync_status: "NOT_SYNCED_FROM_GITHUB",
    });
  }

  const lim = CONTRACT_SPEC_V1.limits;
  const nextTopics = data.next_topics || [];
  for (let i = 0; i < nextTopics.length; i++) {
    const tClean = clean_(nextTopics[i]);
    if (tClean && loopState.next_topics_queue.indexOf(tClean) === -1) {
      loopState.next_topics_queue.push(tClean);
    }
  }
  if (loopState.next_topics_queue.length > lim.max_next_topics_queue) {
    loopState.next_topics_queue = loopState.next_topics_queue.slice(
      -lim.max_next_topics_queue
    );
  }

  const unknowns = data.unknowns || [];
  for (let i = 0; i < unknowns.length; i++) {
    const uClean = clean_(unknowns[i]);
    if (uClean && loopState.open_unknowns.indexOf(uClean) === -1) {
      loopState.open_unknowns.push(uClean);
    }
  }
  if (loopState.open_unknowns.length > lim.max_open_unknowns_queue) {
    loopState.open_unknowns = loopState.open_unknowns.slice(
      -lim.max_open_unknowns_queue
    );
  }

  const indexMd = renderGitHubKnowledgeIndexExportMd_(
    registry,
    localMap,
    remoteMap,
    loopState,
    repoState.freshness || "FRESH_FETCHED"
  );

  if (plannedNew.length > 0 || plannedUpdates.length > 0) {
    filesToCommit[CONTRACT_SPEC_V1.loop_state_file] =
      JSON.stringify(loopState, null, 2) + "\n";
    filesToCommit[CONTRACT_SPEC_V1.github_index_export_file] = indexMd;
  }

  return {
    digest: digest,
    alreadyRecordedInGitHubState: alreadyRecordedInState,
    newRecordsCount: plannedNew.length,
    updatedRecordsCount: plannedUpdates.length,
    newIds: plannedNew.map(function (x) {
      return x.video.video_id;
    }),
    updatedIds: plannedUpdates.map(function (x) {
      return x.video.video_id;
    }),
    skipped: skipped,
    filesToCommit: filesToCommit,
    renderedIndexMd: indexMd,
    updatedLoopState: loopState,
    updatedRegistry: registry,
  };
}

/**
 * Git Database API により複数ファイルを1回の単一コミットで非defaultブランチに保存し、Readback検証を行う
 */
function commitFilesAtomicallyToGitHub_(
  token,
  targetBranch,
  baseCommitSha,
  baseTreeSha,
  filesToCommit,
  commitMessage,
  customFetcher
) {
  const cleanBranch = verifyTargetBranchBoundary_(targetBranch);
  const owner = CONTRACT_SPEC_V1.expected_repo_owner;
  const repo = CONTRACT_SPEC_V1.expected_repo_name;
  const baseRepoPath = "/repos/" + owner + "/" + repo;
  const filePaths = Object.keys(filesToCommit).sort();

  if (filePaths.length === 0) {
    return {
      committed: false,
      headSha: baseCommitSha,
      readbackVerified: true,
      githubWriteStatus: "NO_CHANGES",
    };
  }

  const expectedBlobShas = {};
  const treeEntries = [];

  // 1. 各ファイルの UTF-8 Blob を作成
  for (let i = 0; i < filePaths.length; i++) {
    const path = filePaths[i];
    const blobRes = githubApiRequest_(
      token,
      "post",
      baseRepoPath + "/git/blobs",
      { content: filesToCommit[path], encoding: "utf-8" },
      null,
      customFetcher
    );
    if (blobRes.code !== 201 || !blobRes.json || !blobRes.json.sha) {
      throw new Error(
        "Failed to create git blob for " + path + ": HTTP " + blobRes.code
      );
    }
    expectedBlobShas[path] = blobRes.json.sha;
    treeEntries.push({
      path: path,
      mode: "100644",
      type: "blob",
      sha: blobRes.json.sha,
    });
  }

  // 2. 新しい Git Tree を作成
  const treeRes = githubApiRequest_(
    token,
    "post",
    baseRepoPath + "/git/trees",
    { base_tree: baseTreeSha, tree: treeEntries },
    null,
    customFetcher
  );
  if (treeRes.code !== 201 || !treeRes.json || !treeRes.json.sha) {
    throw new Error("Failed to create git tree: HTTP " + treeRes.code);
  }
  const newTreeSha = treeRes.json.sha;

  // 3. 単一の Git Commit を作成 (parents: [baseCommitSha])
  const newCommitRes = githubApiRequest_(
    token,
    "post",
    baseRepoPath + "/git/commits",
    {
      message: commitMessage,
      tree: newTreeSha,
      parents: [baseCommitSha],
    },
    null,
    customFetcher
  );
  if (newCommitRes.code !== 201 || !newCommitRes.json || !newCommitRes.json.sha) {
    throw new Error("Failed to create git commit: HTTP " + newCommitRes.code);
  }
  const newCommitSha = newCommitRes.json.sha;

  // 4. 非defaultブランチの Ref を force: false で更新 (競合時は HTTP 422 で安全停止、retry=0)
  const refEndpoint =
    baseRepoPath + "/git/refs/heads/" + encodeURI(cleanBranch);
  const patchRes = githubApiRequest_(
    token,
    "patch",
    refEndpoint,
    { sha: newCommitSha, force: false },
    null,
    customFetcher
  );
  if (patchRes.code === 422) {
    return {
      committed: false,
      conflictStopped: true,
      httpCode: 422,
      githubWriteStatus: "STOPPED_ON_BRANCH_CONFLICT_422_NO_OVERWRITE",
      detail: patchRes.text.slice(0, 300),
    };
  }
  if (patchRes.code !== 200) {
    return {
      committed: false,
      conflictStopped: false,
      httpCode: patchRes.code,
      githubWriteStatus: "STOPPED_ON_UNKNOWN_REF_UPDATE_NO_RETRY",
      detail: patchRes.text.slice(0, 300),
    };
  }

  // 5. 即時 Remote Readback 検証 (ブランチHEAD SHA と 全ファイル Blob SHA の一致を確認)
  const readbackRefRes = githubApiRequest_(
    token,
    "get",
    refEndpoint,
    null,
    null,
    customFetcher
  );
  const remoteHeadSha =
    readbackRefRes.json &&
    readbackRefRes.json.object &&
    readbackRefRes.json.object.sha;

  const readbackTreeRes = githubApiRequest_(
    token,
    "get",
    baseRepoPath + "/git/trees/" + newTreeSha + "?recursive=1",
    null,
    null,
    customFetcher
  );
  const remoteBlobMap = {};
  if (
    readbackTreeRes.code === 200 &&
    readbackTreeRes.json &&
    Array.isArray(readbackTreeRes.json.tree)
  ) {
    for (let i = 0; i < readbackTreeRes.json.tree.length; i++) {
      const entry = readbackTreeRes.json.tree[i];
      if (entry.type === "blob") {
        remoteBlobMap[entry.path] = entry.sha;
      }
    }
  }

  let blobsVerified = true;
  for (let i = 0; i < filePaths.length; i++) {
    const p = filePaths[i];
    if (remoteBlobMap[p] !== expectedBlobShas[p]) {
      blobsVerified = false;
      break;
    }
  }

  const readbackVerified = remoteHeadSha === newCommitSha && blobsVerified;
  if (!readbackVerified) {
    throw new Error(
      "Remote readback verification failed: expected commit " +
        newCommitSha +
        ", got " +
        remoteHeadSha
    );
  }

  return {
    committed: true,
    conflictStopped: false,
    headSha: newCommitSha,
    remoteHeadSha: remoteHeadSha,
    fileBlobShas: expectedBlobShas,
    readbackVerified: true,
    githubWriteStatus: "PUSHED_AND_READBACK_VERIFIED",
    notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
  };
}

/**
 * 懸念D対策: Google Drive 上の知識索引エクスポート用ドキュメントを更新し、失敗時は次回実行で自己修復する
 */
function updateDriveExportDocSafely_(exportDocId, indexMarkdownText, customDocApp) {
  if (!exportDocId) {
    return {
      updated: false,
      driveSyncStatus: "SKIPPED_NO_DRIVE_EXPORT_DOC_ID_CONFIGURED",
    };
  }
  const docService =
    customDocApp || (typeof DocumentApp !== "undefined" ? DocumentApp : null);
  if (!docService) {
    throw new Error("DocumentApp service unavailable");
  }
  const doc = docService.openById(exportDocId);
  const docTitle = doc.getName();
  if (docTitle.indexOf("AI技術研究室_知識索引") !== -1) {
    throw new Error(
      "Refusing to overwrite Notebook master index document ('AI技術研究室_知識索引'). Use a separate Google Doc for GitHub export."
    );
  }
  doc.getBody().setText(indexMarkdownText);
  doc.saveAndClose();
  return {
    updated: true,
    docId: exportDocId,
    docTitle: docTitle,
    driveSyncStatus: "DRIVE_EXPORT_DOC_SYNCHRONIZED",
    notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
  };
}

/**
 * メインエントリ1: Google Drive の Inbox フォルダを走査し、GAS内で検証・重複照合・
 * GitHub非defaultブランチへの単一アトミック保存・Readback検証・Drive索引Doc自己修復同期までを完結させる。
 */
function relayDriveReceiptsToGitHub(envOverrides) {
  const overrides = envOverrides || {};
  const lockService =
    overrides.lockService || (typeof LockService !== "undefined" ? LockService : null);
  let scriptLock = null;
  if (lockService && lockService.getScriptLock) {
    scriptLock = lockService.getScriptLock();
    if (!scriptLock.tryLock(5000)) {
      return {
        status: "SKIPPED_CONCURRENT_LOCK_HELD",
        detail: "Another GAS execution is currently holding the ScriptLock.",
      };
    }
  }

  try {
    const props =
      overrides.scriptProperties ||
      (typeof PropertiesService !== "undefined"
        ? PropertiesService.getScriptProperties()
        : null);
    if (!props) {
      throw new Error("PropertiesService unavailable");
    }

    const token = props.getProperty("GITHUB_FINE_GRAINED_PAT");
    const folderId = props.getProperty("DRIVE_INBOX_FOLDER_ID");
    const exportDocId = props.getProperty("DRIVE_EXPORT_DOC_ID");
    const targetBranch = verifyTargetBranchBoundary_(
      props.getProperty("TARGET_GITHUB_BRANCH") ||
        CONTRACT_SPEC_V1.default_target_branch
    );

    if (!token || !folderId) {
      throw new Error(
        "Missing required Script Properties: GITHUB_FINE_GRAINED_PAT and/or DRIVE_INBOX_FOLDER_ID"
      );
    }

    const stateJson = props.getProperty("RELAY_STATE_V1");
    let relayState = {
      processedDigests: {},
      haltedReceipts: {},
      branchCache: {},
      lastGitHubCommitSha: null,
      lastDriveSyncedCommitSha: null,
      pendingDriveSync: false,
    };
    if (stateJson) {
      try {
        relayState = JSON.parse(stateJson);
        if (
          !relayState ||
          typeof relayState !== "object" ||
          !relayState.processedDigests
        ) {
          throw new Error("Invalid RELAY_STATE_V1 structure");
        }
        relayState.haltedReceipts = relayState.haltedReceipts || {};
        relayState.branchCache = relayState.branchCache || {};
      } catch (e) {
        throw new Error(
          "Corrupted RELAY_STATE_V1 in ScriptProperties; refusing to reset state: " +
            e.message
        );
      }
    }

    const driveService =
      overrides.driveApp || (typeof DriveApp !== "undefined" ? DriveApp : null);
    const docService =
      overrides.documentApp ||
      (typeof DocumentApp !== "undefined" ? DocumentApp : null);
    const customFetcher = overrides.urlFetchApp || null;

    const folder = driveService.getFolderById(folderId);
    const files = folder.getFiles();
    const report = [];

    // GitHubの現在状態と他ブランチ増分キャッシュを最初に1回取得
    let repoState = collectGitHubRepositoryState_(
      token,
      targetBranch,
      relayState.branchCache,
      customFetcher
    );
    relayState.branchCache = repoState.branchCache;
    relayState.lastGitHubCommitSha = repoState.targetBranchCommitSha;

    while (files.hasNext()) {
      const file = files.next();
      const mime = file.getMimeType();
      const name = file.getName();
      let rawText = "";

      try {
        if (
          mime === "application/vnd.google-apps.document" ||
          (typeof MimeType !== "undefined" && mime === MimeType.GOOGLE_DOCS)
        ) {
          rawText = docService.openById(file.getId()).getBody().getText();
        } else if (
          mime === "text/plain" ||
          (typeof MimeType !== "undefined" && mime === MimeType.PLAIN_TEXT) ||
          name.endsWith(".json") ||
          name.endsWith(".md") ||
          name.endsWith(".txt")
        ) {
          rawText = file.getBlob().getDataAsString("UTF-8");
        } else {
          continue;
        }
      } catch (readErr) {
        report.push({
          file: name,
          status: "READ_ERROR_SKIPPED",
          detail: String(readErr),
        });
        continue;
      }

      let receiptObj = null;
      try {
        receiptObj = extractReceiptFromText_(rawText);
      } catch (extractErr) {
        report.push({ file: name, status: "SKIPPED_NO_RECEIPT" });
        continue;
      }
      if (
        !receiptObj ||
        receiptObj.schema_version !== CONTRACT_SPEC_V1.receipt_schema_version
      ) {
        report.push({ file: name, status: "SKIPPED_NO_RECEIPT" });
        continue;
      }

      const digest = computeCanonicalSha256_(receiptObj);
      if (relayState.haltedReceipts[digest]) {
        report.push({
          file: name,
          digest: digest,
          status: "HALTED_PREVIOUS_UNKNOWN_WRITE_NEEDS_READBACK",
        });
        continue;
      }

      // 検証と差分計画の作成（禁止キーや不正スキーマはここで拒否され、GitHubには一切送信されない）
      let plan = null;
      try {
        plan = planReceiptApplication_(receiptObj, repoState);
      } catch (valErr) {
        report.push({
          file: name,
          digest: digest,
          status: "REJECTED_VALIDATION_BEFORE_GITHUB_WRITE",
          error: valErr.message || String(valErr),
        });
        continue;
      }

      // 懸念D対策: 前回GitHubコミット成功後にGASが停止していた場合、GitHub正本の loop_state.json から自己修復
      if (plan.alreadyRecordedInGitHubState) {
        if (!relayState.processedDigests[digest]) {
          relayState.processedDigests[digest] = {
            healedAt: new Date().toISOString(),
            sourceFile: name,
            targetBranch: targetBranch,
            githubWriteStatus: "HEALED_FROM_GITHUB_SSOT_ALREADY_COMMITTED",
            notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
          };
          relayState.pendingDriveSync = Boolean(exportDocId);
          props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));
        }
        report.push({
          file: name,
          digest: digest,
          status: "SKIP_DUPLICATE_ALREADY_COMMITTED_ON_GITHUB",
          selfHealed: true,
        });
        continue;
      }

      if (relayState.processedDigests[digest]) {
        report.push({
          file: name,
          digest: digest,
          status: "SKIP_DUPLICATE_ALREADY_PROCESSED",
        });
        continue;
      }

      if (plan.newRecordsCount === 0 && plan.updatedRecordsCount === 0) {
        relayState.processedDigests[digest] = {
          processedAt: new Date().toISOString(),
          sourceFile: name,
          targetBranch: targetBranch,
          githubWriteStatus: "NO_NEW_OR_UPDATED_VIDEOS",
          skipped: plan.skipped,
          notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
        };
        props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));
        report.push({
          file: name,
          digest: digest,
          status: "SKIPPED_ALL_VIDEOS_DUPLICATE_OR_UNVERIFIED",
          skipped: plan.skipped,
        });
        continue;
      }

      const commitMsg =
        "feat(gemini-notebook): atomic cloud ingest of verified receipt " +
        digest.slice(0, 12);
      const commitRes = commitFilesAtomicallyToGitHub_(
        token,
        targetBranch,
        repoState.targetBranchCommitSha,
        repoState.baseTreeSha,
        plan.filesToCommit,
        commitMsg,
        customFetcher
      );

      if (!commitRes.committed) {
        relayState.haltedReceipts[digest] = {
          haltedAt: new Date().toISOString(),
          httpCode: commitRes.httpCode,
          githubWriteStatus: commitRes.githubWriteStatus,
          detail: commitRes.detail,
        };
        props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));
        report.push({
          file: name,
          digest: digest,
          status: commitRes.githubWriteStatus,
          httpCode: commitRes.httpCode,
        });
        break;
      }

      // GitHub保存とReadbackが成功した時点で即座にチェックポイントを保存 (2フェーズ状態管理のPhase 1完了)
      relayState.lastGitHubCommitSha = commitRes.headSha;
      relayState.pendingDriveSync = Boolean(exportDocId);
      relayState.processedDigests[digest] = {
        committedAt: new Date().toISOString(),
        sourceFile: name,
        targetBranch: targetBranch,
        commitSha: commitRes.headSha,
        newVideoIds: plan.newIds,
        updatedVideoIds: plan.updatedIds,
        githubWriteStatus: "PUSHED_AND_READBACK_VERIFIED",
        driveSyncStatus: exportDocId ? "PENDING_DRIVE_UPDATE" : "NOT_CONFIGURED",
        notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
      };
      props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));

      // Phase 2: Google Drive 上の知識索引ドキュメントを更新 (失敗してもGitHubコミットは維持され次回自動復旧)
      let driveStatus = "SKIPPED_NO_DRIVE_EXPORT_DOC_ID_CONFIGURED";
      if (exportDocId) {
        try {
          const driveRes = updateDriveExportDocSafely_(
            exportDocId,
            plan.renderedIndexMd,
            docService
          );
          driveStatus = driveRes.driveSyncStatus;
          relayState.lastDriveSyncedCommitSha = commitRes.headSha;
          relayState.pendingDriveSync = false;
          relayState.processedDigests[digest].driveSyncStatus = driveStatus;
          props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));
        } catch (driveErr) {
          driveStatus = "DRIVE_UPDATE_FAILED_WILL_RECONCILE_NEXT_RUN";
          relayState.pendingDriveSync = true;
          relayState.processedDigests[digest].driveSyncStatus = driveStatus;
          relayState.processedDigests[digest].driveError = String(
            driveErr.message || driveErr
          );
          props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));
        }
      }

      report.push({
        file: name,
        digest: digest,
        status: "COMMITTED_AND_READBACK_VERIFIED",
        commitSha: commitRes.headSha,
        newIds: plan.newIds,
        updatedIds: plan.updatedIds,
        githubWriteStatus: "PUSHED_AND_READBACK_VERIFIED",
        driveSyncStatus: driveStatus,
        notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
        securityPosture: {
          applicationBranchGuard: "ENFORCED_NON_DEFAULT_ONLY",
          targetBranch: targetBranch,
          mainBranchServerProtected: repoState.mainBranchServerProtected,
        },
      });

      // 次のファイル処理のために最新リポジトリ状態を再取得
      repoState = collectGitHubRepositoryState_(
        token,
        targetBranch,
        relayState.branchCache,
        customFetcher
      );
    }

    // 懸念D対策: 新規Receiptが無い実行でも、前回のDrive更新が未完了(pendingDriveSync)または遅延していれば自動修復する
    let driveReconciliation = null;
    if (
      exportDocId &&
      (relayState.pendingDriveSync ||
        relayState.lastDriveSyncedCommitSha !== repoState.targetBranchCommitSha)
    ) {
      const idxPath = CONTRACT_SPEC_V1.github_index_export_file;
      const idxBlobSha = repoState.targetFilesByPath[idxPath];
      if (idxBlobSha) {
        try {
          const latestIndexMd = repoState.fetchBlobTextBySha(idxBlobSha);
          const recRes = updateDriveExportDocSafely_(
            exportDocId,
            latestIndexMd,
            docService
          );
          relayState.lastDriveSyncedCommitSha = repoState.targetBranchCommitSha;
          relayState.pendingDriveSync = false;
          props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));
          driveReconciliation = {
            status: "RECONCILED_FROM_GITHUB_SSOT",
            syncedCommitSha: repoState.targetBranchCommitSha,
            docId: exportDocId,
            driveSyncStatus: recRes.driveSyncStatus,
          };
        } catch (recErr) {
          driveReconciliation = {
            status: "RECONCILE_FAILED_STILL_PENDING",
            error: String(recErr.message || recErr),
          };
        }
      }
    }

    const finalOutput = {
      status: "COMPLETED",
      targetBranch: targetBranch,
      applicationBranchGuard: "ENFORCED_NON_DEFAULT_ONLY",
      mainBranchServerProtected: repoState.mainBranchServerProtected,
      relayReport: report,
      driveReconciliation: driveReconciliation,
      notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
    };
    if (typeof Logger !== "undefined" && Logger.log) {
      Logger.log(JSON.stringify(finalOutput, null, 2));
    }
    return finalOutput;
  } finally {
    if (scriptLock) {
      try {
        scriptLock.releaseLock();
      } catch (e) {}
    }
  }
}

/**
 * メインエントリ2: GitHub非defaultブランチ上の `github_knowledge_index_export.md` を強制取得し、
 * Google Drive上の専用Googleドキュメントを自己修復更新する独立関数。
 */
function pullGitHubIndexExportToDriveDoc(envOverrides) {
  const overrides = envOverrides || {};
  const props =
    overrides.scriptProperties ||
    (typeof PropertiesService !== "undefined"
      ? PropertiesService.getScriptProperties()
      : null);
  const token = props.getProperty("GITHUB_FINE_GRAINED_PAT");
  const exportDocId = props.getProperty("DRIVE_EXPORT_DOC_ID");
  const targetBranch = verifyTargetBranchBoundary_(
    props.getProperty("TARGET_GITHUB_BRANCH") ||
      CONTRACT_SPEC_V1.default_target_branch
  );

  if (!token || !exportDocId) {
    throw new Error("Missing GITHUB_FINE_GRAINED_PAT or DRIVE_EXPORT_DOC_ID");
  }

  const endpoint =
    "/repos/" +
    CONTRACT_SPEC_V1.expected_repo_owner +
    "/" +
    CONTRACT_SPEC_V1.expected_repo_name +
    "/contents/" +
    encodeURIComponent(CONTRACT_SPEC_V1.github_index_export_file) +
    "?ref=" +
    encodeURIComponent(targetBranch);

  const response = githubApiRequest_(
    token,
    "get",
    endpoint,
    null,
    "application/vnd.github.raw+json",
    overrides.urlFetchApp || null
  );
  if (response.code !== 200) {
    throw new Error(
      "Failed to fetch github_knowledge_index_export.md: HTTP " + response.code
    );
  }

  const docRes = updateDriveExportDocSafely_(
    exportDocId,
    response.text,
    overrides.documentApp || null
  );
  return {
    status: "DRIVE_EXPORT_DOC_UPDATED",
    docId: exportDocId,
    docTitle: docRes.docTitle,
    sourceBranch: targetBranch,
    notebookMasterIndexOverwritten: false,
    notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
  };
}

// Node.js 自動テスト環境からのインポート対応 (Python <-> JS 100%互換性検証用)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    CONTRACT_SPEC_V1: CONTRACT_SPEC_V1,
    extractYoutubeId: extractYoutubeId_,
    canonicalYoutubeUrl: canonicalYoutubeUrl_,
    extractReceiptPayload: extractReceiptFromText_,
    computeReceiptDigest: computeCanonicalSha256_,
    scanForbiddenKeys: scanForbiddenKeys_,
    validateReceipt: validateReceipt_,
    renderResearchMarkdown: renderResearchMarkdown_,
    renderDeltaSection: renderDeltaSection_,
    extractVideoIdsFromMarkdownText: extractVideoIdsFromMarkdownText_,
    validateLoopStateSchema: validateLoopStateSchema_,
    renderGitHubKnowledgeIndexExportMd: renderGitHubKnowledgeIndexExportMd_,
    planReceiptApplication: planReceiptApplication_,
    relayDriveReceiptsToGitHub: relayDriveReceiptsToGitHub,
    pullGitHubIndexExportToDriveDoc: pullGitHubIndexExportToDriveDoc,
  };
}

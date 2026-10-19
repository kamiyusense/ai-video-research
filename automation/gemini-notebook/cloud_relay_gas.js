/**
 * AI技術研究室 | Gemini Notebook -> Private GitHub Direct Cloud Bridge (Google Apps Script v0.5)
 *
 * v0.5 における5つの重要改善（別AI独立コードレビュー指摘への完全対応）:
 *   1. GAS ScriptProperties 9KB上限の厳格保護（GitHub正本SSOT化）:
 *      - 処理済みReceipt履歴 (`processed_receipts`) と完了済みリモートブランチキャッシュ (`remote_branch_cache`) は
 *        GitHub正本の `automation/gemini-notebook/state/loop_state.json` 側に保存・参照する。
 *      - GAS の `ScriptProperties` (`RELAY_STATE_V1`) には最小限の揮発制御情報（`lastGitHubCommitSha`,
 *        `lastDriveSyncedCommitSha`, `pendingDriveSync`, 直近のNo-Opダイジェスト最大20件、停止記録最大10件、
 *        未完走スキャンの再開カーソル）のみを保持し、`saveBoundedRelayState_()` で7.5KB以下に強制制限する。
 *   2. 重複検出の完全性保証（ページネーション・Tree truncated検知・分割継続スキャン）:
 *      - `/branches?per_page=100&page=N` を最終ページまで全件ページネーション取得する。
 *      - Git Trees API の `truncated === true` を検知した場合は不完全な照合を拒否して即座に安全停止する。
 *      - 1実行あたりのMarkdown本文Blob読取上限 (`max_blob_fetches_per_run = 25`) に達して未調査ファイルが残った場合、
 *        そのブランチを完了扱い (`scan_complete: true`) にせず、`partialScanProgress` に調査済みパスを記録して
 *        当該実行ではGitHubコミットを保留 (`PAUSED_INCOMPLETE_DEDUP_SCAN_CONTINUES_NEXT_RUN`) し、次回実行で残りを継続走査する。
 *   3. GitHub REST API 公式仕様との完全一致（Commit SHA -> Tree SHA 解決）:
 *      - 対象ブランチだけでなく、すべての他ブランチでも必ず `GET /git/commits/{commit_sha}` から
 *        `tree.sha` を取得したうえで `GET /git/trees/{tree_sha}?recursive=1` を呼び出す。
 *      - 他ブランチのCommit/Tree取得失敗時に無言で `continue` せず、即座にエラー停止する。
 *   4. 文字列値に対する秘密情報・字幕転載パターン検査と限界の明示:
 *      - 禁止キー名だけでなく、すべての文字列フィールドに対してトークン文字列（`ghp_`, `github_pat_`, `AIza`, `sk-`,
 *        `PRIVATE KEY`, `Bearer` 等）、SRT/WebVTT字幕タイムコード、3行連続タイムスタンプ文字起こし、
 *        および過剰な改行（4改行以上）を検査してブロックする。
 *      - ※ただし、タイムスタンプを持たない300字以内の短い丸写しや未知形式の秘匿文字列は機械検査だけでは100%防げないため、
 *        必ず非defaultブランチ（Draft PR）へ隔離保存し、人間の最終レビューを経る設計とする。
 */

const CONTRACT_SPEC_V1 = {
  contract_version: "gemini_notebook_bridge_contract_v1_6",
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
  video_catalog_export_file: "automation/gemini-notebook/state/video_knowledge_catalog.json",
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
  allowed_timestamp_sources: [
    "YOUTUBE_CHAPTER_METADATA",
    "TIMESTAMPED_CAPTIONS",
    "VISUAL_FRAME_CHECK",
    "UNKNOWN",
  ],
  allowed_relation_types: [
    "EXTENDS",
    "UPDATES",
    "COMPLEMENTS",
    "CONTRADICTS",
    "RESOLVES_BACKLOG",
  ],
  allowed_transcript_statuses: [
    "FULL_VERIFIED",
    "PARTIAL_VERIFIED",
    "UNVERIFIED",
    "NOT_ACQUIRED",
    "UNKNOWN",
  ],
  allowed_relation_statuses: [
    "CONFIRMED",
    "CANDIDATE",
    "UNRESOLVED",
  ],
  okf_spec: {
    version: "0.2",
    default_research_doc_type: "RESEARCH_NOTE",
    default_transcript_doc_type: "TRANSCRIPT_SOURCE",
  },
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
  forbidden_value_patterns: [
    {
      id: "GITHUB_TOKEN",
      pattern: "\\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\\b|\\bgithub_pat_[A-Za-z0-9_]{20,}\\b",
      description: "GitHub Personal Access Token or OAuth token",
    },
    {
      id: "GOOGLE_API_OR_OAUTH_TOKEN",
      pattern: "\\bAIza[0-9A-Za-z_-]{30,}\\b|\\bya29\\.[0-9A-Za-z_-]{20,}\\b",
      description: "Google API key or OAuth access token",
    },
    {
      id: "LLM_OR_SAAS_SECRET_KEY",
      pattern: "\\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}\\b|\\bxox[baprs]-[0-9A-Za-z-]{10,}\\b",
      description: "OpenAI, Anthropic, or Slack secret token",
    },
    {
      id: "PRIVATE_KEY_BLOCK",
      pattern: "-----BEGIN [A-Z ]*PRIVATE KEY-----",
      description: "PEM private key block",
    },
    {
      id: "BEARER_AUTH_HEADER",
      pattern: "\\bBearer\\s+[A-Za-z0-9._~+/=-]{20,}\\b",
      description: "Bearer authorization token string",
    },
    {
      id: "SUBTITLE_TIMECODE_BLOCK",
      pattern: "\\bWEBVTT\\b|\\d{1,2}:\\d{2}:\\d{2}[.,]\\d{3}\\s*-->\\s*\\d{1,2}:\\d{2}:\\d{2}",
      description: "WebVTT or SRT subtitle timecode dump",
    },
    {
      id: "MULTILINE_TIMESTAMP_TRANSCRIPT",
      pattern: "(?:^|\\n)\\s*\\[?\\d{1,2}:\\d{2}(?::\\d{2})?\\]?\\s+[^\\n]+\\n\\s*\\[?\\d{1,2}:\\d{2}(?::\\d{2})?\\]?\\s+[^\\n]+\\n\\s*\\[?\\d{1,2}:\\d{2}(?::\\d{2})?\\]?\\s+",
      description: "3+ consecutive timestamped transcript lines",
    },
  ],
  limits: {
    max_videos_per_receipt: 20,
    max_claims_per_video: 12,
    max_title_length: 250,
    max_summary_ja_length: 300,
    max_detailed_findings_length: 2500,
    max_newlines_in_detailed_findings: 25,
    max_chapters_per_video: 25,
    max_chapter_title_length: 150,
    max_chapter_summary_length: 300,
    max_chapter_key_topics: 8,
    max_chapter_key_topic_length: 60,
    max_related_records_per_video: 10,
    max_related_target_id_length: 120,
    max_related_note_length: 250,
    max_source_scope_length: 180,
    max_claim_text_length: 500,
    max_newlines_per_text_field: 3,
    max_next_topics_count: 10,
    max_next_topic_length: 300,
    max_unknowns_count: 20,
    max_unknown_length: 500,
    max_next_topics_queue: 15,
    max_open_unknowns_queue: 25,
    max_blob_fetches_per_run: 25,
    max_script_property_bytes: 7500,
    max_recent_noop_digests: 20,
    max_halted_receipts: 10,
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
const COMPILED_FORBIDDEN_VALUE_PATTERNS = CONTRACT_SPEC_V1.forbidden_value_patterns.map(
  function (item) {
    return {
      id: item.id,
      regex: new RegExp(item.pattern, "m"),
    };
  }
);

function clean_(s) {
  return String(s == null ? "" : s)
    .replace(/\n/g, " ")
    .replace(/\r/g, " ")
    .trim();
}

function utf8ByteLength_(str) {
  const s = String(str || "");
  if (typeof Utilities !== "undefined" && Utilities.newBlob) {
    return Utilities.newBlob(s, "text/plain").getBytes().length;
  }
  if (typeof Buffer !== "undefined") {
    return Buffer.byteLength(s, "utf8");
  }
  return unescape(encodeURIComponent(s)).length;
}

/**
 * 問題1対策: GAS ScriptProperties の1値9KB制限を絶対に超えないよう、サイズを検査・トリムして保存する
 */
function saveBoundedRelayState_(props, relayState) {
  const lim = CONTRACT_SPEC_V1.limits;
  if (!Array.isArray(relayState.recentNoOpDigests)) {
    relayState.recentNoOpDigests = [];
  }
  if (relayState.recentNoOpDigests.length > lim.max_recent_noop_digests) {
    relayState.recentNoOpDigests = relayState.recentNoOpDigests.slice(
      -lim.max_recent_noop_digests
    );
  }
  if (!relayState.haltedReceipts || typeof relayState.haltedReceipts !== "object") {
    relayState.haltedReceipts = {};
  }
  const haltedKeys = Object.keys(relayState.haltedReceipts);
  if (haltedKeys.length > lim.max_halted_receipts) {
    const keepKeys = haltedKeys.slice(-lim.max_halted_receipts);
    const trimmedHalted = {};
    for (let i = 0; i < keepKeys.length; i++) {
      trimmedHalted[keepKeys[i]] = relayState.haltedReceipts[keepKeys[i]];
    }
    relayState.haltedReceipts = trimmedHalted;
  }

  if (!relayState.completedBranchCache || typeof relayState.completedBranchCache !== "object") {
    relayState.completedBranchCache = {};
  }

  let serialized = JSON.stringify(relayState);
  let byteLen = utf8ByteLength_(serialized);

  // 安全サイズ制限（7,500 bytes）を超過した場合の段階的トリム処理
  // 優先順位: 1. recentNoOpDigests -> 2. completedBranchCache -> 3. haltedReceipts
  // ※ partialScanProgress は未完了進捗であり、削除・切り詰めると無限再走査ループに陥るため絶対にトリムしない
  while (byteLen > lim.max_script_property_bytes) {
    if (relayState.recentNoOpDigests.length > 0) {
      relayState.recentNoOpDigests.shift();
    } else if (Object.keys(relayState.completedBranchCache).length > 0) {
      const cKeys = Object.keys(relayState.completedBranchCache);
      delete relayState.completedBranchCache[cKeys[0]];
    } else if (Object.keys(relayState.haltedReceipts).length > 1) {
      const firstKey = Object.keys(relayState.haltedReceipts)[0];
      delete relayState.haltedReceipts[firstKey];
    } else {
      break;
    }
    serialized = JSON.stringify(relayState);
    byteLen = utf8ByteLength_(serialized);
  }

  // 再計算可能なキャッシュを削っても制限に収まらない場合、未完了進捗を破壊して保存するのではなく明確なエラーで停止する
  if (byteLen > lim.max_script_property_bytes) {
    throw new Error(
      "Unable to safely persist partialScanProgress within ScriptProperties byte limit (" +
        byteLen + " > " + lim.max_script_property_bytes +
        " bytes): refusing to corrupt or discard unfinished scan progress"
    );
  }
  props.setProperty("RELAY_STATE_V1", serialized);
  return byteLen;
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

function parseMmssSec_(mmssStr) {
  if (typeof mmssStr !== "string" || mmssStr.indexOf(":") === -1) return null;
  const parts = mmssStr.trim().split(":");
  if (parts.length === 2) {
    const m = parseInt(parts[0], 10);
    const s = parseInt(parts[1], 10);
    return isNaN(m) || isNaN(s) ? null : m * 60 + s;
  }
  if (parts.length === 3) {
    const h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const s = parseInt(parts[2], 10);
    return isNaN(h) || isNaN(m) || isNaN(s) ? null : h * 3600 + m * 60 + s;
  }
  return null;
}

function truncateCleanSummary_(text, maxChars) {
  const limit = maxChars || 295;
  const s = String(text || "").replace(/[\r\n]/g, " ").trim();
  if (s.length <= limit) return s;
  const cut = s.slice(0, limit - 1);
  const lastPunc = Math.max(cut.lastIndexOf("。"), cut.lastIndexOf("、"), cut.lastIndexOf("）"));
  if (lastPunc >= Math.floor(limit / 2)) {
    return cut.slice(0, lastPunc + 1);
  }
  return cut + "…";
}

function inferRelatedRecordsFromContent_(
  vid,
  title,
  summaryJa,
  keyTechList,
  isExistingTarget
) {
  const relations = [];
  const seen = {};
  const maxRel = CONTRACT_SPEC_V1.limits.max_related_records_per_video || 10;
  const maxNote = CONTRACT_SPEC_V1.limits.max_related_note_length || 240;

  function addRel(targetId, relType, note) {
    const key = targetId + "::" + relType;
    if (!seen[key] && relations.length < maxRel) {
      seen[key] = true;
      relations.push({
        target_id: targetId,
        relation: relType,
        note: String(note).slice(0, maxNote),
      });
    }
  }

  if (isExistingTarget) {
    addRel(
      "youtube:" + vid,
      "UPDATES",
      "既存研究記録に対し、Gemini Notebook調査知見・一次メタデータおよび時刻検証結果を差分統合"
    );
  }

  const corpus = (
    String(title || "") +
    " " +
    String(summaryJa || "") +
    " " +
    (Array.isArray(keyTechList) ? keyTechList.join(" ") : "")
  ).toLowerCase();

  if (
    ["eval", "hillclimb", "computer use", "rsi", "自己改善", "判断軸"].some(
      function (kw) {
        return corpus.indexOf(kw) !== -1;
      }
    )
  ) {
    if (vid !== "lC5jxpYmatE") {
      addRel(
        "youtube:lC5jxpYmatE",
        "EXTENDS",
        "課題ドリブン・Skill・Computer Use・ハーネス設計に対する評価・自己改善・実行ループを拡張"
      );
    }
    addRel(
      "proposal:P006",
      "COMPLEMENTS",
      "未解決課題ストック(P006)の再評価・検証ループ設計を補完"
    );
  } else if (
    [
      "playwright",
      "1password",
      "prompt caching",
      "キャッシュ",
      "ウォレット",
      "秘密鍵",
      "hooks",
      "skill",
      "スキル",
    ].some(function (kw) {
      return corpus.indexOf(kw) !== -1;
    })
  ) {
    if (vid !== "lC5jxpYmatE") {
      addRel(
        "youtube:lC5jxpYmatE",
        "COMPLEMENTS",
        "Skill・ハーネス・権限分離・トークン節約の実務構成を補完"
      );
    }
  }

  if (
    [
      "サブエージェント",
      "マルチエージェント",
      "agents.md",
      "memory.md",
      "コーディネーター",
      "右腕",
      "スペシャリスト",
      "サブスレッド",
    ].some(function (kw) {
      return corpus.indexOf(kw) !== -1;
    })
  ) {
    if (vid !== "Vr3JkAT9mo8") {
      addRel(
        "youtube:Vr3JkAT9mo8",
        "COMPLEMENTS",
        "AGENTS.md・MEMORY.md・専門サブエージェント分業アーキテクチャを補完"
      );
    }
  }

  if (
    ["obsidian", "vault", "llm wiki"].some(function (kw) {
      return corpus.indexOf(kw) !== -1;
    })
  ) {
    if (vid !== "BStkW1HTfmk") {
      addRel(
        "youtube:BStkW1HTfmk",
        "COMPLEMENTS",
        "ObsidianローカルVaultによる長期記憶・ナレッジ構造化設計を補完"
      );
    }
  }

  if (
    ["notebooklm", "gemini notebook", "studio"].some(function (kw) {
      return corpus.indexOf(kw) !== -1;
    })
  ) {
    if (vid !== "ZjUJ-35acaU") {
      addRel(
        "youtube:ZjUJ-35acaU",
        "COMPLEMENTS",
        "Gemini Notebook / NotebookLMへの情報集約・Studio出力・知識索引運用を補完"
      );
    }
  }

  return relations;
}

function normalizeGeminiHandoffReceipt_(data, options) {
  if (!data || typeof data !== "object" || Array.isArray(data)) return data;
  if (data.schema_version === CONTRACT_SPEC_V1.receipt_schema_version) return data;
  if (data.receipt_version !== CONTRACT_SPEC_V1.receipt_schema_version) return data;

  const opts = options || {};
  const evidenceMap =
    opts.evidenceMap && typeof opts.evidenceMap === "object"
      ? opts.evidenceMap
      : {};

  scanForbiddenKeys_(data, "root");

  if (!Object.prototype.hasOwnProperty.call(data, "videos")) {
    if (data.video_ids || data.split_files) {
      throw new Error(
        "Master index file (video_ids/split_files without videos array) is not an executable batch receipt; process PART1 and PART2 batch files instead."
      );
    }
    throw new Error("Missing videos array in Gemini handoff receipt");
  }
  if (!Array.isArray(data.videos) || data.videos.length > 20) {
    throw new Error("videos must be a list of <=20 items");
  }

  const batchPart = String(data.batch_part || "1/2").trim();
  const batchDesc = String(data.batch_description || "").trim();
  const isPart2 = batchPart.indexOf("2") === 0 || batchDesc.indexOf("過去") !== -1;
  const genAt = String(data.checked_at || data.generated_at || "");
  const checkedAt = genAt.length >= 10 ? genAt.slice(0, 10) : "2026-10-17";

  const notebookUrl = String(
    data.notebook_url ||
      opts.defaultNotebookUrl ||
      CONTRACT_SPEC_V1.default_notebook_url
  ).trim();

  const rootSourceId = String(
    data.notebook_source_id ||
      data.source_title ||
      data.notebook_source ||
      opts.defaultNotebookSourceId ||
      ""
  ).trim();

  const topRbRaw = String(data.notebook_readback || "UNKNOWN")
    .trim()
    .toUpperCase();
  const topReadback =
    CONTRACT_SPEC_V1.allowed_readback.indexOf(topRbRaw) !== -1
      ? topRbRaw
      : "UNKNOWN";

  const convertedVideos = [];
  const topUnknowns = [];

  for (let i = 0; i < data.videos.length; i++) {
    const rv = data.videos[i];
    if (!rv || typeof rv !== "object") {
      throw new Error("Invalid video entry in Gemini handoff receipt");
    }
    const vid = rv.video_id || rv.id;
    if (typeof vid !== "string" || !VIDEO_ID_RE.test(vid)) {
      throw new Error("Invalid video_id in Gemini handoff receipt: " + vid);
    }
    const url = rv.url || canonicalYoutubeUrl_(vid);
    const title = String(rv.title || "").trim();
    const pubDate = String(rv.published_at || rv.publish_date || "").trim() || null;
    const rawSummary = String(rv.summary_ja || rv.summary || "").trim();
    const summaryJa = truncateCleanSummary_(rawSummary, 295);

    const evRec =
      evidenceMap[vid] && typeof evidenceMap[vid] === "object"
        ? evidenceMap[vid]
        : null;
    const durStr = String(rv.duration || "UNKNOWN").trim();
    const durSec = parseMmssSec_(durStr);
    const ytLen =
      evRec && typeof evRec.yt_len_sec === "number" ? evRec.yt_len_sec : null;
    const ytPub = evRec && evRec.yt_pub ? String(evRec.yt_pub) : null;
    const ytTitle = evRec && evRec.yt_title ? String(evRec.yt_title) : null;
    const ytAuthor = evRec && evRec.yt_author ? String(evRec.yt_author) : null;
    const contradictsDesc = Boolean(evRec && evRec.contradicts_desc);
    const evChapters =
      evRec && evRec.chapters && typeof evRec.chapters === "object"
        ? evRec.chapters
        : {};
    const durMatch = Boolean(
      ytLen !== null &&
        durSec !== null &&
        Math.abs(durSec - ytLen) <= 2 &&
        evRec.dur_match !== false
    );

    const chapters = [];
    const longChapterTitles = [];
    if (Array.isArray(rv.timeline)) {
      for (let j = 0; j < rv.timeline.length; j++) {
        const tl = rv.timeline[j];
        const sStr = String(tl.start || "");
        const eStr = String(tl.end || "");
        const sCalc = parseMmssSec_(sStr);
        const eCalc = parseMmssSec_(eStr);
        const repSec = tl.seconds;
        const tlLink = String(tl.link || "");
        const tlTitle = String(tl.title || "").trim();
        if (
          sCalc === null ||
          eCalc === null ||
          typeof repSec !== "number" ||
          sCalc !== repSec ||
          eCalc < sCalc ||
          (tlLink && tlLink.indexOf("t=" + repSec + "s") === -1)
        ) {
          throw new Error("Timeline timestamp/seconds/link mismatch in " + vid);
        }
        if (tlTitle.length > 150) {
          longChapterTitles.push(sStr + "〜" + eStr + ": " + tlTitle);
        }

        const chEv = evChapters[String(sCalc)];
        const verdict = chEv && chEv.verdict ? String(chEv.verdict) : null;
        const inRange = ytLen !== null && eCalc <= ytLen + 2;

        let tsSource = "UNKNOWN";
        let eFinal = null;
        if (evRec !== null && durMatch && !contradictsDesc && inRange) {
          if (verdict === "DESC_MATCH") {
            tsSource = "YOUTUBE_CHAPTER_METADATA";
            eFinal = Math.min(eCalc, ytLen);
          } else if (verdict === "CAPTION_PASS") {
            tsSource = "TIMESTAMPED_CAPTIONS";
            eFinal = Math.min(eCalc, ytLen);
          }
        }

        const keyTechs = (Array.isArray(rv.key_technologies) ? rv.key_technologies : [])
          .map(function (k) {
            return String(k || "").trim();
          })
          .filter(Boolean);
        let matchedTopics = keyTechs.filter(function (kt) {
          return tlTitle.toLowerCase().indexOf(kt.toLowerCase()) !== -1;
        });
        if (matchedTopics.length === 0) {
          matchedTopics = keyTechs.slice(0, 3);
        }
        matchedTopics = matchedTopics.slice(0, 8).map(function (kt) {
          return kt.slice(0, 60);
        });

        if (tsSource !== "UNKNOWN") {
          chapters.push({
            title: tlTitle.slice(0, 150),
            start_seconds: sCalc,
            end_seconds: eFinal,
            summary_ja: ("区間 " + sStr + "〜" + eStr + " の解説: " + tlTitle).slice(0, 300),
            timestamp_source: tsSource,
            key_topics: matchedTopics,
          });
        } else {
          chapters.push({
            title: tlTitle.slice(0, 150),
            start_seconds: null,
            end_seconds: null,
            summary_ja: (
              "Gemini報告区間(" + sStr + "〜" + eStr + " / 一次時刻未確認のため再生リンク非生成): " + tlTitle
            ).slice(0, 300),
            timestamp_source: "UNKNOWN",
            key_topics: matchedTopics,
          });
        }
      }
    }

    const videoSourceId = String(
      rv.notebook_source_id ||
        rv.source_title ||
        rv.notebook_source ||
        rootSourceId
    ).trim();
    if (!videoSourceId) {
      throw new Error(
        "Missing notebook_source_id/source_title for video " +
          vid +
          " in Gemini handoff receipt; refusing to guess source name"
      );
    }

    const rawScope = String(rv.source_scope || data.source_scope || "").trim();
    let sourceScope = "";
    if (rawScope) {
      sourceScope =
        rawScope.indexOf("NOTEBOOK_SOURCE:") !== -1
          ? rawScope
          : rawScope + " | NOTEBOOK_SOURCE:" + videoSourceId;
    } else {
      sourceScope =
        (isPart2
          ? "GEMINI_PAST_RESEARCH_NOTE_AND_OFFICIAL_DOCS"
          : "YOUTUBE_TRANSCRIPT_AND_OFFICIAL_DOCS") +
        " | NOTEBOOK_SOURCE:" +
        videoSourceId;
    }

    const vidRbRaw = String(
      rv.notebook_readback || data.notebook_readback || "UNKNOWN"
    )
      .trim()
      .toUpperCase();
    const vidReadback =
      CONTRACT_SPEC_V1.allowed_readback.indexOf(vidRbRaw) !== -1
        ? vidRbRaw
        : "UNKNOWN";

    const ov = rv.official_verification || {};
    const ovDetails = String(ov.details || "").trim();
    const ovUrl = String(ov.official_url || ov.url || "").trim() || null;
    const ovStatusRaw = String(ov.status || "").trim().toUpperCase();
    const constraints = String(rv.constraints_and_notes || "").trim();
    const futureApps = String(rv.future_applications || "").trim();
    const unkStr = String(rv.unknowns || "").trim();
    const channelStr = String(rv.channel || "UNKNOWN").trim();
    const numStr = String(rv.number || "").trim();
    const resDate = String(rv.research_date || checkedAt).trim();
    const keyTechList = (Array.isArray(rv.key_technologies) ? rv.key_technologies : [])
      .map(function (k) {
        return String(k || "").trim();
      })
      .filter(Boolean);

    const claims = [];
    if (ovDetails) {
      let claimStatus = "REPORTED_BY_AUTHOR";
      let claimUrl = null;
      let prefix = "[Gemini公式照合報告(一次URL未添付・要独立確認)] ";
      if (
        ovUrl &&
        validUrl_(ovUrl) &&
        (ovStatusRaw === "VERIFIED" || ovStatusRaw === "CONFIRMED_DOC")
      ) {
        claimStatus = "CONFIRMED_DOC";
        claimUrl = ovUrl;
        prefix = isPart2
          ? "[PART2研究ノート経由・一次公式URL照合済] "
          : "[PART1直近調査・一次公式URL照合済] ";
      } else if (ovStatusRaw === "UNKNOWN") {
        claimStatus = "UNKNOWN";
        claimUrl = ovUrl && validUrl_(ovUrl) ? ovUrl : null;
      }
      claims.push({
        text: (prefix + ovDetails).slice(0, 500),
        status: claimStatus,
        timestamp_seconds: null,
        timestamp_source: "UNKNOWN",
        official_url: claimUrl,
      });
    }
    if (constraints || futureApps) {
      claims.push({
        text: ("制約・注意点: " + constraints + " / 今後の応用: " + futureApps).slice(0, 500),
        status: "REPORTED_BY_AUTHOR",
        timestamp_seconds: null,
        timestamp_source: "UNKNOWN",
        official_url: null,
      });
    }
    if (unkStr) {
      claims.push({
        text: ("未確認事項(UNKNOWN): " + unkStr).slice(0, 500),
        status: "UNKNOWN",
        timestamp_seconds: null,
        timestamp_source: "UNKNOWN",
        official_url: null,
      });
      topUnknowns.push((vid + " (No." + numStr + "): " + unkStr).slice(0, 500));
    }

    let nDesc = 0;
    let nCap = 0;
    let nUnk = 0;
    for (let cIdx = 0; cIdx < chapters.length; cIdx++) {
      if (chapters[cIdx].timestamp_source === "YOUTUBE_CHAPTER_METADATA") nDesc += 1;
      else if (chapters[cIdx].timestamp_source === "TIMESTAMPED_CAPTIONS") nCap += 1;
      else nUnk += 1;
    }

    const finalPubDate = ytPub
      ? pubDate === ytPub
        ? ytPub + " (YouTube一次確認一致)"
        : ytPub + " (YouTube一次確認 / Gemini記載値: " + (pubDate || "UNKNOWN") + ")"
      : pubDate;

    const dfLines = [
      "- 整理番号・区分: No." +
        numStr +
        " (" +
        (batchDesc || batchPart) +
        ") / 投稿者(Gemini記載): " +
        channelStr +
        " / 調査日: " +
        resDate,
    ];
    if (evRec !== null && ytLen !== null) {
      const titleCmp =
        ytTitle && title === ytTitle
          ? "一致"
          : "不一致(YouTube一次=「" +
            (ytTitle || "UNKNOWN") +
            "」 vs Gemini記載=「" +
            title +
            "」)";
      const authorCmp =
        ytAuthor && channelStr === ytAuthor
          ? "一致"
          : "不一致(YouTube一次=「" +
            (ytAuthor || "UNKNOWN") +
            "」 vs Gemini記載=「" +
            channelStr +
            "」)";
      const durCmp = durMatch ? "一致(±2s以内)" : "不一致";
      const pubCmp = ytPub && pubDate === ytPub ? "一致" : "不一致";
      const ytMm = String(Math.floor(ytLen / 60)).padStart(2, "0");
      const ytSs = String(ytLen % 60).padStart(2, "0");
      dfLines.push(
        "- YouTube一次メタデータ照合: タイトル=" +
          titleCmp +
          " / 投稿者=" +
          authorCmp
      );
      dfLines.push(
        "- 動画長・公開日一次照合: YouTube一次実測長=" +
          ytMm +
          ":" +
          ytSs +
          " (" +
          ytLen +
          "s) vs Gemini記載長=" +
          durStr +
          " (" +
          durCmp +
          ") | YouTube一次公開日=" +
          (ytPub || "UNKNOWN") +
          " vs Gemini記載公開日=" +
          (pubDate || "UNKNOWN") +
          " (" +
          pubCmp +
          ")"
      );
    } else {
      dfLines.push(
        "- 動画長・公開日照合: Gemini記載長=" +
          durStr +
          ", 記載公開日=" +
          (pubDate || "UNKNOWN") +
          " (YouTube一次検証データ未登録のため全チャプター時刻をUNKNOWN扱い)"
      );
    }

    dfLines.push(
      "- チャプター時刻一次検証内訳: 全" +
        chapters.length +
        "章中 概要欄チャプター一致(YOUTUBE_CHAPTER_METADATA)=" +
        nDesc +
        "章, 字幕語彙一致(TIMESTAMPED_CAPTIONS)=" +
        nCap +
        "章, 一次根拠未確認(UNKNOWN)=" +
        nUnk +
        "章"
    );
    dfLines.push(
      "- 証拠強度区分: " +
        (!isPart2
          ? "PART1（Notebook内のYouTubeソース由来・章別一次照合適用）"
          : "PART2（Gemini過去研究ノート由来・章別一次照合適用）")
    );
    dfLines.push("- 全体要約（原文保持）: " + rawSummary);
    dfLines.push(
      "- 主要技術キーワード: " +
        (keyTechList.length ? keyTechList.join(", ") : "NONE")
    );
    dfLines.push(
      "- 公式仕様・一次資料照合報告（一次URL未添付時はREPORTED_BY_AUTHOR扱い）: " +
        (ovDetails || "UNKNOWN")
    );
    dfLines.push("- 制約・注意点: " + (constraints || "UNKNOWN"));
    dfLines.push("- 今後の応用・自動化案: " + (futureApps || "UNKNOWN"));
    dfLines.push("- 未確認事項（UNKNOWN）: " + (unkStr || "UNKNOWN"));
    if (longChapterTitles.length > 0) {
      dfLines.push(
        "- 長文チャプタータイトル原文保持: " + longChapterTitles.join(" / ")
      );
    }
    if (evRec && evRec.desc_summary) {
      dfLines.push(
        "- YouTube概要欄の公式チャプター（一次照合参照用）: " +
          evRec.desc_summary
      );
    }

    const isExistingTarget = vid === "ZjUJ-35acaU" || vid === "BStkW1HTfmk";
    const relatedRecords =
      rv.related_records ||
      inferRelatedRecordsFromContent_(
        vid,
        title,
        rawSummary,
        keyTechList,
        isExistingTarget
      );

    convertedVideos.push({
      video_id: vid,
      title: title.slice(0, 250),
      url: url,
      published_at: finalPubDate,
      summary_ja: summaryJa,
      detailed_findings_ja: dfLines.join("\n").slice(0, 2500),
      chapters: chapters,
      source_scope: sourceScope.slice(0, 180),
      claims: claims,
      related_records: relatedRecords,
      notebook_source_id: videoSourceId,
      notebook_readback: vidReadback,
      changes: rv.changes || (isExistingTarget ? ["UPDATED"] : ["NEW"]),
    });
  }

  return {
    schema_version: CONTRACT_SPEC_V1.receipt_schema_version,
    notebook_url: notebookUrl,
    checked_at: checkedAt,
    notebook_readback: topReadback,
    github_dedup_status: "UNKNOWN",
    next_topics: data.next_topics || [],
    unknowns: topUnknowns.slice(0, 20),
    videos: convertedVideos,
  };
}

function isHandoffValidationError_(e) {
  if (!e || !e.message) return false;
  const msg = String(e.message);
  return (
    msg.indexOf("Master index file") !== -1 ||
    msg.indexOf("Timeline timestamp") !== -1 ||
    msg.indexOf("Forbidden") !== -1 ||
    msg.indexOf("Missing notebook_source_id") !== -1 ||
    msg.indexOf("Missing videos array") !== -1 ||
    msg.indexOf("videos must be a list") !== -1 ||
    msg.indexOf("Invalid video_id") !== -1
  );
}

function extractReceiptFromText_(rawText, options) {
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
        (data.schema_version === CONTRACT_SPEC_V1.receipt_schema_version ||
          data.receipt_version === CONTRACT_SPEC_V1.receipt_schema_version)
      ) {
        return normalizeGeminiHandoffReceipt_(data, options);
      }
    } catch (e) {
      if (isHandoffValidationError_(e)) throw e;
    }
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
        (data.schema_version === CONTRACT_SPEC_V1.receipt_schema_version ||
          data.receipt_version === CONTRACT_SPEC_V1.receipt_schema_version)
      ) {
        return normalizeGeminiHandoffReceipt_(data, options);
      }
    } catch (e) {
      if (isHandoffValidationError_(e)) throw e;
    }
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
                  (data.schema_version === CONTRACT_SPEC_V1.receipt_schema_version ||
                    data.receipt_version === CONTRACT_SPEC_V1.receipt_schema_version)
                ) {
                  return normalizeGeminiHandoffReceipt_(data, options);
                }
              } catch (e) {
                if (isHandoffValidationError_(e)) throw e;
              }
              break;
            }
          }
        }
      }
      start = start > 0 ? rawText.lastIndexOf("{", start - 1) : -1;
    }
  }
  return normalizeGeminiHandoffReceipt_(JSON.parse(stripped), options);
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
  const crypto = require("crypto");
  return crypto.createHash("sha256").update(canonicalJson, "utf8").digest("hex");
}

/**
 * 問題5対策: 禁止キー名だけでなく、すべての文字列値に対して秘密情報パターン・字幕タイムコード・文字起こし塊を検査する
 */
function scanForbiddenKeys_(val, path) {
  const curPath = path || "root";
  if (val === null || val === undefined) return;
  if (typeof val === "string") {
    for (let i = 0; i < COMPILED_FORBIDDEN_VALUE_PATTERNS.length; i++) {
      const rule = COMPILED_FORBIDDEN_VALUE_PATTERNS[i];
      if (rule.regex.test(val)) {
        throw new Error(
          "Forbidden content pattern (" +
            rule.id +
            ") in receipt payload at " +
            curPath
        );
      }
    }
    return;
  }
  if (typeof val !== "object") return;
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

function countNewlines_(s) {
  return (String(s || "").match(/\n/g) || []).length;
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
    if (countNewlines_(v.summary_ja) > lim.max_newlines_per_text_field) {
      throw new Error(
        "Summary contains too many line breaks (possible transcript dump)"
      );
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
      typeof v.notebook_source_id !== "string" ||
      v.notebook_source_id.trim().length < 1 ||
      v.notebook_source_id.length > 120
    ) {
      throw new Error("Invalid notebook_source_id");
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
      if (countNewlines_(c.text) > lim.max_newlines_per_text_field) {
        throw new Error(
          "Claim text contains too many line breaks (possible transcript dump)"
        );
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
      const tsSource = c.timestamp_source;
      if (tsSource !== undefined && tsSource !== null) {
        if (CONTRACT_SPEC_V1.allowed_timestamp_sources.indexOf(tsSource) === -1) {
          throw new Error("Invalid claim timestamp_source");
        }
        if (tsSource === "UNKNOWN" && t !== undefined && t !== null) {
          throw new Error(
            "Claim with UNKNOWN timestamp_source cannot specify timestamp_seconds"
          );
        }
        if (tsSource !== "UNKNOWN" && (t === undefined || t === null)) {
          throw new Error(
            "Claim with verified timestamp_source must specify timestamp_seconds"
          );
        }
      }
      const u = c.official_url;
      if (u !== undefined && u !== null && !validUrl_(u)) {
        throw new Error("Invalid official_url");
      }
      if (c.status === "CONFIRMED_DOC" && !validUrl_(u)) {
        throw new Error(
          "Claim with CONFIRMED_DOC status requires a valid official_url"
        );
      }
    }

    // v0.6 optional field: detailed_findings_ja
    if (v.detailed_findings_ja !== undefined && v.detailed_findings_ja !== null) {
      if (
        typeof v.detailed_findings_ja !== "string" ||
        v.detailed_findings_ja.trim().length < 1 ||
        v.detailed_findings_ja.length > lim.max_detailed_findings_length
      ) {
        throw new Error("Invalid detailed_findings_ja");
      }
      if (
        countNewlines_(v.detailed_findings_ja) >
        lim.max_newlines_in_detailed_findings
      ) {
        throw new Error(
          "detailed_findings_ja contains too many line breaks (possible transcript dump)"
        );
      }
    }

    // v0.6 optional field: chapters
    if (v.chapters !== undefined && v.chapters !== null) {
      if (
        !Array.isArray(v.chapters) ||
        v.chapters.length > lim.max_chapters_per_video
      ) {
        throw new Error("chapters must be a list of <=25 items");
      }
      for (let k = 0; k < v.chapters.length; k++) {
        const ch = v.chapters[k];
        if (!ch || typeof ch !== "object" || Array.isArray(ch)) {
          throw new Error("Invalid chapter entry");
        }
        if (
          typeof ch.title !== "string" ||
          ch.title.trim().length < 1 ||
          ch.title.length > lim.max_chapter_title_length ||
          ch.title.indexOf("\n") !== -1
        ) {
          throw new Error("Invalid chapter title");
        }
        if (
          typeof ch.summary_ja !== "string" ||
          ch.summary_ja.trim().length < 1 ||
          ch.summary_ja.length > lim.max_chapter_summary_length ||
          countNewlines_(ch.summary_ja) > lim.max_newlines_per_text_field
        ) {
          throw new Error("Invalid chapter summary_ja");
        }
        if (
          CONTRACT_SPEC_V1.allowed_timestamp_sources.indexOf(
            ch.timestamp_source
          ) === -1
        ) {
          throw new Error("Invalid chapter timestamp_source");
        }
        const sSec = ch.start_seconds;
        const eSec = ch.end_seconds;
        const sDefined = sSec !== undefined && sSec !== null;
        const eDefined = eSec !== undefined && eSec !== null;
        if (
          sDefined &&
          (typeof sSec !== "number" ||
            !Number.isInteger(sSec) ||
            typeof sSec === "boolean" ||
            sSec < 0)
        ) {
          throw new Error("Invalid chapter start_seconds");
        }
        if (
          eDefined &&
          (typeof eSec !== "number" ||
            !Number.isInteger(eSec) ||
            typeof eSec === "boolean" ||
            eSec < 0)
        ) {
          throw new Error("Invalid chapter end_seconds");
        }
        if (ch.timestamp_source === "UNKNOWN" && (sDefined || eDefined)) {
          throw new Error(
            "Chapter with UNKNOWN timestamp_source cannot specify start_seconds/end_seconds"
          );
        }
        if (ch.timestamp_source !== "UNKNOWN" && !sDefined) {
          throw new Error(
            "Chapter with verified timestamp_source must specify start_seconds"
          );
        }
        if (!sDefined && eDefined) {
          throw new Error("Chapter end_seconds requires start_seconds");
        }
        if (sDefined && eDefined && eSec < sSec) {
          throw new Error("Chapter end_seconds must be >= start_seconds");
        }
        if (ch.key_topics !== undefined && ch.key_topics !== null) {
          if (
            !Array.isArray(ch.key_topics) ||
            ch.key_topics.length > lim.max_chapter_key_topics ||
            !ch.key_topics.every(function (kt) {
              return (
                typeof kt === "string" &&
                kt.trim().length >= 1 &&
                kt.trim().length <= lim.max_chapter_key_topic_length &&
                kt.indexOf("\n") === -1
              );
            })
          ) {
            throw new Error("Invalid chapter key_topics");
          }
        }
      }
    }

    // v0.6 optional field: related_records
    if (v.related_records !== undefined && v.related_records !== null) {
      if (
        !Array.isArray(v.related_records) ||
        v.related_records.length > lim.max_related_records_per_video
      ) {
        throw new Error("related_records must be a list of <=10 items");
      }
      for (let m = 0; m < v.related_records.length; m++) {
        const rel = v.related_records[m];
        if (!rel || typeof rel !== "object" || Array.isArray(rel)) {
          throw new Error("Invalid related_record entry");
        }
        if (
          typeof rel.target_id !== "string" ||
          rel.target_id.trim().length < 1 ||
          rel.target_id.length > lim.max_related_target_id_length ||
          rel.target_id.indexOf("\n") !== -1
        ) {
          throw new Error("Invalid related_record target_id");
        }
        if (CONTRACT_SPEC_V1.allowed_relation_types.indexOf(rel.relation) === -1) {
          throw new Error("Invalid related_record relation");
        }
        if (
          typeof rel.note !== "string" ||
          rel.note.trim().length < 1 ||
          rel.note.length > lim.max_related_note_length ||
          countNewlines_(rel.note) > lim.max_newlines_per_text_field
        ) {
          throw new Error("Invalid related_record note");
        }
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
    const tsSource = c.timestamp_source;
    let timeRef = "UNKNOWN";
    if (t !== undefined && t !== null && tsSource !== "UNKNOWN") {
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
    let line =
      "- " +
      clean_(c.text) +
      " | " +
      c.status +
      " | time: " +
      timeRef +
      " | official: " +
      (c.official_url || "UNKNOWN");
    if (tsSource !== undefined && tsSource !== null) {
      line += " | time_source: " + tsSource;
    }
    lines.push(line);
  }
  return lines;
}

function formatChaptersLines_(vid, chapters) {
  const lines = [];
  const list = Array.isArray(chapters) ? chapters : [];
  for (let i = 0; i < list.length; i++) {
    const ch = list[i];
    const sSec = ch.start_seconds;
    const eSec = ch.end_seconds;
    const tsSource = ch.timestamp_source || "UNKNOWN";
    let timeLink = "UNKNOWN";
    if (sSec !== undefined && sSec !== null && tsSource !== "UNKNOWN") {
      const startMmss = pad2_(Math.floor(sSec / 60)) + ":" + pad2_(sSec % 60);
      let rangeLabel = startMmss;
      if (eSec !== undefined && eSec !== null) {
        rangeLabel =
          startMmss + "〜" + pad2_(Math.floor(eSec / 60)) + ":" + pad2_(eSec % 60);
      }
      timeLink =
        "[" +
        rangeLabel +
        "](https://www.youtube.com/watch?v=" +
        vid +
        "&t=" +
        sSec +
        "s)";
    }
    const topics = Array.isArray(ch.key_topics) ? ch.key_topics : [];
    const topicsStr =
      topics.length > 0 ? topics.map(clean_).join(", ") : "NONE";
    lines.push(
      "- " +
        timeLink +
        " | **" +
        clean_(ch.title) +
        "** | " +
        clean_(ch.summary_ja) +
        " | time_source: " +
        tsSource +
        " | topics: " +
        topicsStr
    );
  }
  return lines;
}

function formatDetailedFindingsLines_(detailedFindingsJa) {
  if (!detailedFindingsJa) return [];
  const normalized = String(detailedFindingsJa)
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .trim();
  return normalized.split("\n").map(function (line) {
    return line.replace(/[ \t]+$/, "");
  });
}

function formatRelatedRecordsLines_(relatedRecords) {
  const lines = [];
  const list = Array.isArray(relatedRecords) ? relatedRecords : [];
  for (let i = 0; i < list.length; i++) {
    const rel = list[i];
    const tid = clean_(rel.target_id);
    const targetPath = clean_(rel.target_path || rel.path || "");
    const status = rel.status ? String(rel.status) : "";
    let targetRepr = "`" + tid + "`";
    if (targetPath && status.toUpperCase() !== "UNRESOLVED" && status.toUpperCase() !== "CANDIDATE") {
      targetRepr = "[" + tid + "](" + targetPath + ")";
    }
    let line =
      "- " +
      targetRepr +
      " (" +
      rel.relation +
      "): " +
      clean_(rel.note);
    if (rel.status) {
      line += " | status: " + rel.status;
    }
    if (rel.evidence) {
      line += " | evidence: " + clean_(rel.evidence);
    }
    lines.push(line);
  }
  return lines;
}

function renderOkfFrontmatter_(v, checkedAt) {
  const vid = v.video_id;
  const canon = canonicalYoutubeUrl_(vid);
  const rawTitle = clean_(v.title);
  const titleDisplay = rawTitle.startsWith("【研究カード】")
    ? rawTitle
    : "【研究カード】 " + rawTitle;
  const nbSrc = clean_(v.notebook_source_id || "UNKNOWN");
  const logicalId = clean_(v.logical_id || ("youtube:" + vid + ":research"));
  const transcriptLogicalId = clean_(v.transcript_logical_id || ("youtube:" + vid + ":transcript"));
  const transcriptStatus = clean_(v.transcript_status || "UNKNOWN");

  let lines = [
    "---",
    'okf_version: "0.2"',
    'type: "RESEARCH_NOTE"',
    "title: " + JSON.stringify(titleDisplay),
    "description: " + JSON.stringify(clean_(v.summary_ja)),
    "resource: " + JSON.stringify(canon),
    "tags:",
    '  - "AI技術研究室"',
    '  - "動画研究"',
    "logical_id: " + JSON.stringify(logicalId),
    "record_id: " + JSON.stringify("youtube:" + vid),
    "video_id: " + JSON.stringify(vid),
    "canonical_url: " + JSON.stringify(canon),
    "original_url: " + JSON.stringify(v.url),
    "publication_date: " + JSON.stringify(clean_(v.published_at || "UNKNOWN")),
    "checked_at: " + JSON.stringify(checkedAt),
    "source_scope: " + JSON.stringify(clean_(v.source_scope)),
    "transcript_logical_id: " + JSON.stringify(transcriptLogicalId),
    "transcript_status: " + JSON.stringify(transcriptStatus),
    "primary_source_notebook_id: " + JSON.stringify(nbSrc),
    'document_type: "AI技術研究室 構造化研究カード（二次分析資料）"',
    "notebook_readback: " + JSON.stringify(v.notebook_readback),
    'github_verification: "NOT_RUN"',
    'github_to_notebook_sync: "NOT_SYNCED_FROM_GITHUB"',
    "changes:",
  ];
  const changes = Array.isArray(v.changes) ? v.changes : [];
  for (let i = 0; i < changes.length; i++) {
    lines.push("  - " + JSON.stringify(changes[i]));
  }
  const rels = Array.isArray(v.related_records) ? v.related_records : [];
  if (rels.length > 0) {
    lines.push("related_records:");
    for (let i = 0; i < rels.length; i++) {
      const rel = rels[i];
      lines.push("  - target_id: " + JSON.stringify(clean_(rel.target_id)));
      lines.push("    relation: " + JSON.stringify(rel.relation));
      lines.push("    note: " + JSON.stringify(clean_(rel.note)));
      const st = rel.status || "CANDIDATE";
      lines.push("    status: " + JSON.stringify(st));
      if (rel.evidence) {
        lines.push("    evidence: " + JSON.stringify(clean_(rel.evidence)));
      }
    }
  }
  lines.push("---");
  return lines;
}

function renderResearchMarkdown_(v, checkedAt) {
  const vid = v.video_id;
  const rawTitle = clean_(v.title);
  const titleDisplay = rawTitle.startsWith("【研究カード】")
    ? rawTitle
    : "【研究カード】 " + rawTitle;

  let lines = renderOkfFrontmatter_(v, checkedAt);
  lines = lines.concat([
    "",
    "# " + titleDisplay,
    "",
    "> [!IMPORTANT]",
    "> **文書区分**: 本ドキュメントは一次資料（YouTube字幕）を基に構造化分析した「AI技術研究室 研究カード」です。Notebook内の一次資料YouTube動画そのものではありません。回答引用時は「一次資料（動画）」と「本研究カード（構造化分析）」を明確に区別してください。",
    "",
    "## 独自要約",
    clean_(v.summary_ja),
  ]);
  if (Array.isArray(v.chapters) && v.chapters.length > 0) {
    lines = lines.concat([
      "",
      "## 動画目次・確認済みタイムライン（チャプター）",
    ]);
    lines = lines.concat(formatChaptersLines_(vid, v.chapters));
  }
  if (v.detailed_findings_ja) {
    lines = lines.concat([
      "",
      "## 詳細技術知識・再利用ノート",
    ]);
    lines = lines.concat(formatDetailedFindingsLines_(v.detailed_findings_ja));
  }
  lines = lines.concat([
    "",
    "## 主張・一次資料・時刻",
  ]);
  lines = lines.concat(formatClaimsLines_(vid, v.claims));
  if (Array.isArray(v.related_records) && v.related_records.length > 0) {
    lines = lines.concat([
      "",
      "## 関連する既存研究・課題との接続",
    ]);
    lines = lines.concat(formatRelatedRecordsLines_(v.related_records));
  }
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
  const nbSrc = clean_(v.notebook_source_id || "UNKNOWN");
  const logicalId = clean_(v.logical_id || ("youtube:" + vid + ":research"));
  const transcriptLogicalId = clean_(v.transcript_logical_id || ("youtube:" + vid + ":transcript"));
  const transcriptStatus = clean_(v.transcript_status || "UNKNOWN");
  let lines = [
    "",
    "## 差分更新 (" + checkedAt + " / " + changesStr + ")",
    "",
    "- checked_at: " + checkedAt,
    "- source_scope: " + clean_(v.source_scope),
    "- logical_id: `" + logicalId + "`",
    "- transcript_logical_id: `" + transcriptLogicalId + "`",
    "- transcript_status: " + transcriptStatus,
    "- primary_source_notebook_id: " + nbSrc,
    "- Gemini Notebook source (一次資料YouTube動画): " + nbSrc,
    "- document_type: AI技術研究室 構造化研究カード（二次分析資料）",
    "- okf_version: 0.2",
    "- Gemini readback (self-reported): " + v.notebook_readback,
    "- GitHub-to-Notebook reverse sync: NOT_SYNCED_FROM_GITHUB",
    "- changes: " + changesStr,
    "",
    "### 差分要約",
    clean_(v.summary_ja),
  ];
  if (Array.isArray(v.chapters) && v.chapters.length > 0) {
    lines = lines.concat([
      "",
      "### 追加・更新された動画目次・タイムライン",
    ]);
    lines = lines.concat(formatChaptersLines_(vid, v.chapters));
  }
  if (v.detailed_findings_ja) {
    lines = lines.concat([
      "",
      "### 追加・更新された詳細技術知識",
    ]);
    lines = lines.concat(formatDetailedFindingsLines_(v.detailed_findings_ja));
  }
  lines = lines.concat([
    "",
    "### 追加・更新された主張と検証",
  ]);
  lines = lines.concat(formatClaimsLines_(vid, v.claims));
  if (Array.isArray(v.related_records) && v.related_records.length > 0) {
    lines = lines.concat([
      "",
      "### 追加・更新された関連研究・課題接続",
    ]);
    lines = lines.concat(formatRelatedRecordsLines_(v.related_records));
  }
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
 * 問題1・問題2・問題3への完全対応:
 *   - `/branches` の全ページ取得 (per_page=100 & page=1,2,...)
 *   - 全ブランチで公式仕様通り `GET /git/commits/{commit_sha}` から `tree.sha` を解決して `GET /git/trees/{tree_sha}?recursive=1` を呼ぶ
 *   - `tree.truncated === true` 時は不完全照合を拒否して即座に例外停止
 *   - GitHub正本の `loop_state.json.remote_branch_cache` (SSOT) と GASの一時再開カーソル `partialScanProgress` を組み合わせ、
 *     `max_blob_fetches_per_run` (25件) で打ち切った場合は `dedupScanComplete = false` として次回実行へ進捗を引き継ぐ（未完走のままPASSにしない）
 */
function collectGitHubRepositoryState_(
  token,
  targetBranch,
  partialScanProgress,
  customFetcher,
  completedBranchCache
) {
  const owner = CONTRACT_SPEC_V1.expected_repo_owner;
  const repo = CONTRACT_SPEC_V1.expected_repo_name;
  const baseRepoPath = "/repos/" + owner + "/" + repo;

  // 1. 全ブランチ一覧を最終ページまでページネーション取得 (問題2対策)
  const allBranchesRaw = [];
  let page = 1;
  while (true) {
    const branchesRes = githubApiRequest_(
      token,
      "get",
      baseRepoPath + "/branches?per_page=100&page=" + page,
      null,
      null,
      customFetcher
    );
    if (branchesRes.code !== 200 || !Array.isArray(branchesRes.json)) {
      throw new Error(
        "Failed to fetch fresh remote branches (page " +
          page +
          ", HTTP " +
          branchesRes.code +
          "): refusing to trust stale state"
      );
    }
    for (let i = 0; i < branchesRes.json.length; i++) {
      allBranchesRaw.push(branchesRes.json[i]);
    }
    if (branchesRes.json.length < 100) {
      break;
    }
    page += 1;
    if (page > 50) {
      throw new Error("Exceeded safe branch pagination limit (>5000 branches)");
    }
  }

  let mainBranchServerProtected = false;
  let targetBranchCommitSha = null;
  const remoteBranches = [];

  for (let i = 0; i < allBranchesRaw.length; i++) {
    const b = allBranchesRaw[i];
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

  function resolveCommitTreeSha(commitSha, branchLabel) {
    const cRes = githubApiRequest_(
      token,
      "get",
      baseRepoPath + "/git/commits/" + commitSha,
      null,
      null,
      customFetcher
    );
    if (cRes.code !== 200 || !cRes.json || !cRes.json.tree || !cRes.json.tree.sha) {
      throw new Error(
        "Failed to resolve git commit tree SHA for " +
          branchLabel +
          " (" +
          commitSha +
          "): HTTP " +
          cRes.code
      );
    }
    return cRes.json.tree.sha;
  }

  function fetchRecursiveTreeByTreeSha(treeSha, branchLabel) {
    const tRes = githubApiRequest_(
      token,
      "get",
      baseRepoPath + "/git/trees/" + treeSha + "?recursive=1",
      null,
      null,
      customFetcher
    );
    if (tRes.code !== 200 || !tRes.json || !Array.isArray(tRes.json.tree)) {
      throw new Error(
        "Failed to read git tree for " +
          branchLabel +
          " (" +
          treeSha +
          "): HTTP " +
          tRes.code
      );
    }
    if (tRes.json.truncated === true) {
      throw new Error(
        "Git tree for " +
          branchLabel +
          " (" +
          treeSha +
          ") is truncated (exceeds GitHub recursive tree limit); refusing incomplete duplicate detection"
      );
    }
    return tRes.json.tree;
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

  // 2. TargetブランチのCommit -> Tree SHA解決とRecursive Tree取得 (truncated検査付き)
  const baseTreeSha = resolveCommitTreeSha(targetBranchCommitSha, targetBranch);
  const targetTreeItems = fetchRecursiveTreeByTreeSha(baseTreeSha, targetBranch);

  const targetFilesByPath = {};
  for (let i = 0; i < targetTreeItems.length; i++) {
    const item = targetTreeItems[i];
    if (item.type === "blob") {
      targetFilesByPath[item.path] = item.sha;
    }
  }

  // 3. Targetブランチの registry.json と loop_state.json (GitHub正本SSOT) を取得・検証
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

  const githubBranchCache =
    loopState.remote_branch_cache && typeof loopState.remote_branch_cache === "object"
      ? JSON.parse(JSON.stringify(loopState.remote_branch_cache))
      : {};
  const activeCompletedBranchCache =
    completedBranchCache && typeof completedBranchCache === "object"
      ? JSON.parse(JSON.stringify(completedBranchCache))
      : {};
  const nextPartialProgress =
    partialScanProgress && typeof partialScanProgress === "object"
      ? JSON.parse(JSON.stringify(partialScanProgress))
      : {};

  let blobFetchesUsed = 0;
  const maxBlobFetches = CONTRACT_SPEC_V1.limits.max_blob_fetches_per_run;
  let remainingUnscannedFiles = 0;

  // 4. Targetブランチ内の localMap 構築（未走査本文があれば分割継続カーソルを利用）
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

  const targetProgressKey = "target:" + targetBranch;
  let targetPartial = nextPartialProgress[targetProgressKey];
  if (!targetPartial || targetPartial.commit_sha !== targetBranchCommitSha) {
    targetPartial = {
      commit_sha: targetBranchCommitSha,
      scanned_paths: {},
      videos: [],
    };
  }
  for (let i = 0; i < targetPartial.videos.length; i++) {
    const pv = targetPartial.videos[i];
    if (pv && pv.video_id && !localMap[pv.video_id]) {
      localMap[pv.video_id] = pv;
    }
  }

  const targetPaths = Object.keys(targetFilesByPath).sort();
  let targetAllBodiesScanned = true;
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
    if (relPath.startsWith("notes/") || !mName) {
      if (targetPartial.scanned_paths[relPath]) {
        continue;
      }
      if (blobFetchesUsed < maxBlobFetches) {
        blobFetchesUsed += 1;
        const body = fetchBlobTextBySha(targetFilesByPath[relPath]);
        const bodyVids = extractVideoIdsFromMarkdownText_(body);
        for (let k = 0; k < bodyVids.length; k++) {
          const bVid = bodyVids[k];
          const vEntry = {
            video_id: bVid,
            source: "body:" + relPath,
            research_path: relPath,
            status: "REFERENCED_IN_RESEARCH_OR_NOTE_BODY",
          };
          targetPartial.videos.push(vEntry);
          if (!localMap[bVid]) {
            localMap[bVid] = vEntry;
          }
        }
        targetPartial.scanned_paths[relPath] = true;
      } else {
        targetAllBodiesScanned = false;
        remainingUnscannedFiles += 1;
      }
    }
  }
  if (targetAllBodiesScanned) {
    delete nextPartialProgress[targetProgressKey];
  } else {
    nextPartialProgress[targetProgressKey] = targetPartial;
  }

  // 5. 他ブランチ (origin/*) の完全性保証付き照合（問題2・問題3対策）
  const remoteMap = {};
  remoteBranches.sort(function (a, b) {
    return a.ref < b.ref ? -1 : a.ref > b.ref ? 1 : 0;
  });

  function mergeRemoteEntry(ref, entry) {
    const vid = entry.video_id;
    if (!vid || !VIDEO_ID_RE.test(vid)) return;
    if (!remoteMap[vid]) {
      remoteMap[vid] = {
        video_id: vid,
        canonical_url: entry.canonical_url || canonicalYoutubeUrl_(vid),
        research_path: entry.research_path || "",
        status: entry.status || "UNKNOWN",
        detected_via: entry.detected_via || "remote",
        branches: [],
      };
    }
    if (remoteMap[vid].branches.indexOf(ref) === -1) {
      remoteMap[vid].branches.push(ref);
    }
  }

  for (let i = 0; i < remoteBranches.length; i++) {
    const rb = remoteBranches[i];
    const cachedOnGitHub = githubBranchCache[rb.ref];
    const cachedInGas = activeCompletedBranchCache[rb.ref];
    const cached =
      cachedOnGitHub && cachedOnGitHub.commit_sha === rb.commitSha && cachedOnGitHub.scan_complete === true
        ? cachedOnGitHub
        : cachedInGas && cachedInGas.commit_sha === rb.commitSha && cachedInGas.scan_complete === true
        ? cachedInGas
        : null;

    // 完全走査済み (scan_complete === true) かつ同一 Commit SHA の場合のみキャッシュヒットとする
    if (cached) {
      const cachedVideos = Array.isArray(cached.videos)
        ? cached.videos
        : Array.isArray(cached.video_ids)
        ? cached.video_ids.map(function (v) { return { video_id: v }; })
        : [];
      for (let j = 0; j < cachedVideos.length; j++) {
        const cv = cachedVideos[j];
        const cEntry = typeof cv === "string" ? { video_id: cv } : cv;
        mergeRemoteEntry(rb.ref, cEntry);
      }
      delete nextPartialProgress[rb.ref];
      continue;
    }

    // 問題3対策: 必ず Commit SHA から公式の Tree SHA を解決してから Git Tree を取得する
    const rbTreeSha = resolveCommitTreeSha(rb.commitSha, rb.ref);
    const rbTreeItems = fetchRecursiveTreeByTreeSha(rbTreeSha, rb.ref);

    const rbBlobs = {};
    for (let j = 0; j < rbTreeItems.length; j++) {
      const tItem = rbTreeItems[j];
      if (tItem.type === "blob") {
        rbBlobs[tItem.path] = tItem.sha;
      }
    }

    let rbPartial = nextPartialProgress[rb.ref];
    if (!rbPartial || rbPartial.commit_sha !== rb.commitSha) {
      rbPartial = {
        commit_sha: rb.commitSha,
        tree_sha: rbTreeSha,
        registry_scanned: false,
        scanned_paths: {},
        videos_by_id: {},
      };
    }

    if (rbBlobs["registry.json"] && !rbPartial.registry_scanned) {
      const rbRegRaw = fetchBlobTextBySha(rbBlobs["registry.json"]);
      let rbReg;
      try {
        rbReg = JSON.parse(rbRegRaw);
      } catch (e) {
        throw new Error(
          "Corrupted registry.json on remote branch " + rb.ref + ": " + e.message
        );
      }
      const recs = rbReg.records || [];
      for (let j = 0; j < recs.length; j++) {
        const rec = recs[j];
        if (rec && VIDEO_ID_RE.test(String(rec.video_id || ""))) {
          const vid = rec.video_id;
          if (!rbPartial.videos_by_id[vid]) {
            rbPartial.videos_by_id[vid] = {
              video_id: vid,
              canonical_url: rec.canonical_url || canonicalYoutubeUrl_(vid),
              research_path: rec.research_path || "",
              status: rec.status || "UNKNOWN",
              detected_via: "registry.json",
            };
          }
        }
      }
      rbPartial.registry_scanned = true;
    }

    const rbPaths = Object.keys(rbBlobs).sort();
    let rbAllScanned = true;
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
        if (!rbPartial.videos_by_id[vid]) {
          rbPartial.videos_by_id[vid] = {
            video_id: vid,
            canonical_url: canonicalYoutubeUrl_(vid),
            research_path: relPath,
            status: "REMOTE_RESEARCH_FILE",
            detected_via: "filename:" + relPath,
          };
        }
      }
      if (relPath.startsWith("notes/") || !mName) {
        if (rbPartial.scanned_paths[relPath]) {
          continue;
        }
        if (blobFetchesUsed < maxBlobFetches) {
          blobFetchesUsed += 1;
          const body = fetchBlobTextBySha(rbBlobs[relPath]);
          const bodyVids = extractVideoIdsFromMarkdownText_(body);
          for (let k = 0; k < bodyVids.length; k++) {
            const bVid = bodyVids[k];
            if (!rbPartial.videos_by_id[bVid]) {
              rbPartial.videos_by_id[bVid] = {
                video_id: bVid,
                canonical_url: canonicalYoutubeUrl_(bVid),
                research_path: relPath,
                status: "REMOTE_MARKDOWN_REFERENCE",
                detected_via: "body:" + relPath,
              };
            }
          }
          rbPartial.scanned_paths[relPath] = true;
        } else {
          rbAllScanned = false;
          remainingUnscannedFiles += 1;
        }
      }
    }

    const rbVideoList = Object.keys(rbPartial.videos_by_id).map(function (k) {
      return rbPartial.videos_by_id[k];
    });
    for (let j = 0; j < rbVideoList.length; j++) {
      mergeRemoteEntry(rb.ref, rbVideoList[j]);
    }

    if (rbAllScanned) {
      // 全対象ファイルの走査が完了した場合のみ scan_complete: true としてキャッシュ昇格する
      const vidList = rbVideoList.map(function (v) { return v.video_id; });
      githubBranchCache[rb.ref] = {
        commit_sha: rb.commitSha,
        tree_sha: rbTreeSha,
        scan_complete: true,
        videos: rbVideoList,
      };
      activeCompletedBranchCache[rb.ref] = {
        commit_sha: rb.commitSha,
        tree_sha: rbTreeSha,
        scan_complete: true,
        videos: rbVideoList,
        video_ids: vidList,
      };
      delete nextPartialProgress[rb.ref];
    } else {
      // 未調査ファイルが残っている場合は絶対に scan_complete: true にせず、次回へ進捗を引き継ぐ
      nextPartialProgress[rb.ref] = rbPartial;
    }
  }

  const dedupScanComplete = remainingUnscannedFiles === 0;
  loopState.remote_branch_cache = githubBranchCache;

  let timestampEvidence = {};
  const tsEvPath = "automation/gemini-notebook/state/timestamp_evidence.json";
  if (targetFilesByPath[tsEvPath]) {
    try {
      const tsEvRaw = fetchBlobTextBySha(targetFilesByPath[tsEvPath]);
      const tsEvParsed = JSON.parse(tsEvRaw);
      if (
        tsEvParsed &&
        tsEvParsed.schema_version === "timestamp_evidence_v1" &&
        tsEvParsed.videos &&
        typeof tsEvParsed.videos === "object"
      ) {
        timestampEvidence = tsEvParsed.videos;
      }
    } catch (e) {}
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
    timestampEvidence: timestampEvidence,
    freshness: dedupScanComplete ? "FRESH_FETCHED" : "INCOMPLETE_PARTIAL_SCAN",
    dedupScanComplete: dedupScanComplete,
    remainingUnscannedFiles: remainingUnscannedFiles,
    partialScanProgress: nextPartialProgress,
    completedBranchCache: activeCompletedBranchCache,
    mainBranchServerProtected: mainBranchServerProtected,
    fetchBlobTextBySha: fetchBlobTextBySha,
  };
}

function planReceiptApplication_(data, repoState) {
  const videos = validateReceipt_(data);
  const digest = computeCanonicalSha256_(data);

  if (repoState.dedupScanComplete === false) {
    throw new Error(
      "Duplicate detection scan is incomplete (" +
        repoState.remainingUnscannedFiles +
        " unscanned markdown files remaining); refusing to treat deduplication as PASS"
    );
  }

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

      if (v.notebook_readback === "FAIL") {
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
    const rbStatusTag =
      v.notebook_readback === "PASS"
        ? "NOTEBOOK_READBACK_SELF_REPORTED_ONLY"
        : "NOTEBOOK_READBACK_UNKNOWN";
    const recEntry = {
      record_id: "youtube:" + v.video_id,
      video_id: v.video_id,
      canonical_url: canonicalYoutubeUrl_(v.video_id),
      research_path: item.path,
      source_scope: v.source_scope,
      research_date: data.checked_at,
      status:
        "GEMINI_REPORTED; " +
        rbStatusTag +
        "; GITHUB_SAVED; NOTEBOOK_MASTER_INDEX_SYNC_SEPARATE",
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
 * 下流受け渡し省力化:
 * GitHubへコミットした各研究Markdown（research/*.md）を、Google Driveの出力先フォルダ
 * （DRIVE_OUTPUT_FOLDER_ID、未設定時はDRIVE_INBOX_FOLDER_ID）へ自動配置・同期する。
 * これにより、ユーザーはGitHubからの手動DL・手動UPなしでNotebookLMのDrive選択から即追加できる。
 */
function syncResearchCardsToDriveSafely_(driveService, folderId, filesToCommit, isDryRun) {
  if (!driveService || !folderId || !Array.isArray(filesToCommit)) {
    return {
      status: "SKIPPED_NO_DRIVE_FOLDER_OR_FILES",
      syncedCards: [],
    };
  }
  const cardFiles = [];
  for (let i = 0; i < filesToCommit.length; i++) {
    const f = filesToCommit[i];
    if (f.path && f.path.indexOf("research/") === 0 && f.path.endsWith(".md")) {
      const parts = f.path.split("/");
      const baseName = parts[parts.length - 1];
      const cardFileName = "【研究カード】_" + baseName;
      cardFiles.push({
        path: f.path,
        fileName: cardFileName,
        content: f.content,
      });
    }
  }
  if (cardFiles.length === 0) {
    return {
      status: "NO_RESEARCH_CARDS_TO_SYNC",
      syncedCards: [],
    };
  }
  if (isDryRun) {
    return {
      status: "DRY_RUN_PREVIEW_ONLY_NO_DRIVE_WRITE",
      syncedCards: cardFiles.map(function(c) {
        return { fileName: c.fileName, path: c.path, action: "WOULD_SYNC" };
      }),
    };
  }
  const folder = driveService.getFolderById(folderId);
  const results = [];
  const plainTextMime =
    typeof MimeType !== "undefined" && MimeType.PLAIN_TEXT
      ? MimeType.PLAIN_TEXT
      : "text/plain";

  for (let i = 0; i < cardFiles.length; i++) {
    const c = cardFiles[i];
    const existing = folder.getFilesByName(c.fileName);
    if (existing.hasNext()) {
      const file = existing.next();
      file.setContent(c.content);
      results.push({
        fileName: c.fileName,
        path: c.path,
        fileId: file.getId(),
        action: "UPDATED",
      });
    } else {
      const newFile = folder.createFile(c.fileName, c.content, plainTextMime);
      results.push({
        fileName: c.fileName,
        path: c.path,
        fileId: newFile.getId(),
        action: "CREATED",
      });
    }
  }
  return {
    status: "DRIVE_CARDS_SYNCHRONIZED",
    syncedCards: results,
  };
}

/**
 * メインエントリ1: Google Drive の Inbox フォルダを走査し、GAS内で検証・完全重複照合・
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

    const token =
      props.getProperty("GITHUB_FINE_GRAINED_PAT") ||
      props.getProperty("GITHUB_PAT");
    const folderId = props.getProperty("DRIVE_INBOX_FOLDER_ID");
    const outputFolderId =
      props.getProperty("DRIVE_OUTPUT_FOLDER_ID") || folderId;
    const exportDocId = props.getProperty("DRIVE_EXPORT_DOC_ID");
    const targetBranch = verifyTargetBranchBoundary_(
      props.getProperty("TARGET_GITHUB_BRANCH") ||
        props.getProperty("TARGET_BRANCH") ||
        CONTRACT_SPEC_V1.default_target_branch
    );
    const isDryRun = Boolean(
      overrides.dryRun === true ||
        props.getProperty("DRY_RUN") === "true" ||
        props.getProperty("DRY_RUN") === "1"
    );

    if (!token || !folderId) {

      throw new Error(
        "Missing required Script Properties: GITHUB_FINE_GRAINED_PAT (or GITHUB_PAT) and/or DRIVE_INBOX_FOLDER_ID"
      );
    }

    // 問題1対策: RELAY_STATE_V1 は軽量な揮発状態のみを保持し、過去全履歴はGitHub正本の loop_state.json を参照する
    const stateJson = props.getProperty("RELAY_STATE_V1");
    let relayState = {
      schemaVersion: "gas_relay_compact_state_v2",
      lastGitHubCommitSha: null,
      lastDriveSyncedCommitSha: null,
      pendingDriveSync: false,
      recentNoOpDigests: [],
      haltedReceipts: {},
      partialScanProgress: {},
      completedBranchCache: {},
    };
    if (stateJson) {
      try {
        const parsed = JSON.parse(stateJson);
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("Invalid RELAY_STATE_V1 structure");
        }
        relayState.lastGitHubCommitSha = parsed.lastGitHubCommitSha || null;
        relayState.lastDriveSyncedCommitSha = parsed.lastDriveSyncedCommitSha || null;
        relayState.pendingDriveSync = Boolean(parsed.pendingDriveSync);
        relayState.recentNoOpDigests = Array.isArray(parsed.recentNoOpDigests)
          ? parsed.recentNoOpDigests
          : [];
        relayState.haltedReceipts =
          parsed.haltedReceipts && typeof parsed.haltedReceipts === "object"
            ? parsed.haltedReceipts
            : {};
        relayState.partialScanProgress =
          parsed.partialScanProgress &&
          typeof parsed.partialScanProgress === "object"
            ? parsed.partialScanProgress
            : {};
        relayState.completedBranchCache =
          parsed.completedBranchCache &&
          typeof parsed.completedBranchCache === "object"
            ? parsed.completedBranchCache
            : {};
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

    let repoState = collectGitHubRepositoryState_(
      token,
      targetBranch,
      relayState.partialScanProgress,
      customFetcher,
      relayState.completedBranchCache
    );
    relayState.partialScanProgress = repoState.partialScanProgress;
    relayState.completedBranchCache = repoState.completedBranchCache;
    relayState.lastGitHubCommitSha = repoState.targetBranchCommitSha;
    const stateBytesAfterScan = saveBoundedRelayState_(props, relayState);

    // 問題2対策: 未走査のMarkdown本文が残っている場合は、重複確認PASSとみなさず次回実行へ進捗を引き継いで安全一時停止する
    if (!repoState.dedupScanComplete) {
      const pausedOutput = {
        status: "PAUSED_INCOMPLETE_DEDUP_SCAN_CONTINUES_NEXT_RUN",
        mode: isDryRun ? "DRY_RUN" : "APPLY",
        targetBranch: targetBranch,
        dedupScanComplete: false,
        remainingUnscannedFiles: repoState.remainingUnscannedFiles,
        scriptPropertyBytesUsed: stateBytesAfterScan,
        notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
      };
      if (typeof Logger !== "undefined" && Logger.log) {
        Logger.log(JSON.stringify(pausedOutput, null, 2));
      }
      return pausedOutput;
    }

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
        receiptObj = extractReceiptFromText_(rawText, {
          evidenceMap: repoState.timestampEvidence || {},
          defaultNotebookUrl:
            (repoState.loopState && repoState.loopState.notebook_url) ||
            CONTRACT_SPEC_V1.default_notebook_url,
        });
      } catch (extractErr) {
        if (isHandoffValidationError_(extractErr)) {
          report.push({
            file: name,
            status: "REJECTED_VALIDATION_BEFORE_GITHUB_WRITE",
            error: extractErr.message || String(extractErr),
          });
        } else {
          report.push({ file: name, status: "SKIPPED_NO_RECEIPT" });
        }
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

      // GitHub正本の loop_state.json に既に記録されている場合は重複コミットせず、Drive同期が未完なら自己修復へ進む
      if (plan.alreadyRecordedInGitHubState) {
        if (
          exportDocId &&
          relayState.lastDriveSyncedCommitSha !== repoState.targetBranchCommitSha
        ) {
          relayState.pendingDriveSync = true;
          saveBoundedRelayState_(props, relayState);
        }
        report.push({
          file: name,
          digest: digest,
          status: "SKIP_DUPLICATE_ALREADY_COMMITTED_ON_GITHUB",
          selfHealed: true,
        });
        continue;
      }

      if (relayState.recentNoOpDigests.indexOf(digest) !== -1) {
        report.push({
          file: name,
          digest: digest,
          status: "SKIP_DUPLICATE_NOOP_RECEIPT",
        });
        continue;
      }

      if (plan.newRecordsCount === 0 && plan.updatedRecordsCount === 0) {
        relayState.recentNoOpDigests.push(digest);
        saveBoundedRelayState_(props, relayState);
        report.push({
          file: name,
          digest: digest,
          status: "SKIPPED_ALL_VIDEOS_DUPLICATE_OR_UNVERIFIED",
          skipped: plan.skipped,
        });
        continue;
      }

      if (isDryRun) {
        let dryRunCards = { status: "SKIPPED_DRY_RUN", syncedCards: [] };
        try {
          dryRunCards = syncResearchCardsToDriveSafely_(
            driveService,
            outputFolderId,
            plan.filesToCommit,
            true
          );
        } catch (dErr) {
          dryRunCards = { status: "PREVIEW_ERROR", error: String(dErr) };
        }
        report.push({
          file: name,
          digest: digest,
          status: "DRY_RUN_PREVIEW_ONLY_NO_GITHUB_WRITE",
          wouldCommit: true,
          newRecordsCount: plan.newRecordsCount,
          updatedRecordsCount: plan.updatedRecordsCount,
          newIds: plan.newIds,
          updatedIds: plan.updatedIds,
          skipped: plan.skipped,
          driveCardSyncPreview: dryRunCards,
          githubWriteStatus: "PREVIEW_ONLY",
          notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
          securityPosture: {
            applicationBranchGuard: "ENFORCED_NON_DEFAULT_ONLY",
            targetBranch: targetBranch,
            mainBranchServerProtected: repoState.mainBranchServerProtected,
          },
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
          status: commitRes.githubWriteStatus,
        };
        saveBoundedRelayState_(props, relayState);
        report.push({
          file: name,
          digest: digest,
          status: commitRes.githubWriteStatus,
          httpCode: commitRes.httpCode,
        });
        break;
      }

      relayState.lastGitHubCommitSha = commitRes.headSha;
      relayState.pendingDriveSync = Boolean(exportDocId);
      saveBoundedRelayState_(props, relayState);

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
          saveBoundedRelayState_(props, relayState);
        } catch (driveErr) {
          driveStatus = "DRIVE_UPDATE_FAILED_WILL_RECONCILE_NEXT_RUN";
          relayState.pendingDriveSync = true;
          saveBoundedRelayState_(props, relayState);
        }
      }

      let driveCardSync = { status: "SKIPPED_NO_DRIVE_FOLDER_OR_FILES", syncedCards: [] };
      try {
        driveCardSync = syncResearchCardsToDriveSafely_(
          driveService,
          outputFolderId,
          plan.filesToCommit,
          false
        );
      } catch (cardErr) {
        driveCardSync = {
          status: "DRIVE_CARD_SYNC_FAILED",
          error: String(cardErr.message || cardErr),
        };
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
        driveCardSyncStatus: driveCardSync,
        notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
        securityPosture: {
          applicationBranchGuard: "ENFORCED_NON_DEFAULT_ONLY",
          targetBranch: targetBranch,
          mainBranchServerProtected: repoState.mainBranchServerProtected,
        },
      });

      repoState = collectGitHubRepositoryState_(
        token,
        targetBranch,
        relayState.partialScanProgress,
        customFetcher
      );
      relayState.partialScanProgress = repoState.partialScanProgress;
    }

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
          saveBoundedRelayState_(props, relayState);
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

    const finalBytes = saveBoundedRelayState_(props, relayState);
    const finalOutput = {
      status: "COMPLETED",
      mode: isDryRun ? "DRY_RUN" : "APPLY",
      targetBranch: targetBranch,
      applicationBranchGuard: "ENFORCED_NON_DEFAULT_ONLY",
      mainBranchServerProtected: repoState.mainBranchServerProtected,
      dedupScanComplete: repoState.dedupScanComplete,
      scriptPropertyBytesUsed: finalBytes,
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
 * Dry-Run（書き込み前プレビュー検証）エントリポイント:
 * Google Drive 内の Receipt を取得・検証・重複照合するが、
 * GitHub へのコミット・書き込みは一切行わずに安全停止する。
 * GASエディタから安全に事前検証を行うための公開関数（末尾アンダースコアなし）。
 */
function runCloudRelayDryRun(envOverrides) {
  const overrides = envOverrides || {};
  overrides.dryRun = true;
  return relayDriveReceiptsToGitHub(overrides);
}

/**
 * 手順書 (`PC_OFF_OPERATIONS.md`) との完全互換エントリポイント:
 * 時間主導型トリガーから直接呼び出される関数（公開関数: 末尾アンダースコアなし）。
 * GASのトリガー設定ダイアログ・エディタ実行ドロップダウンに表示されます。
 */
function runCloudRelayLoop(envOverrides) {
  return relayDriveReceiptsToGitHub(envOverrides);
}


/**
 * 互換用エイリアス（旧ドキュメント指定用）
 */
function runCloudRelayLoop_(envOverrides) {
  return relayDriveReceiptsToGitHub(envOverrides);
}

function pullGitHubIndexExportToDriveDoc(envOverrides) {
  const overrides = envOverrides || {};
  const props =
    overrides.scriptProperties ||
    (typeof PropertiesService !== "undefined"
      ? PropertiesService.getScriptProperties()
      : null);
  const token =
    props.getProperty("GITHUB_FINE_GRAINED_PAT") ||
    props.getProperty("GITHUB_PAT");
  const exportDocId = props.getProperty("DRIVE_EXPORT_DOC_ID");
  const targetBranch = verifyTargetBranchBoundary_(
    props.getProperty("TARGET_GITHUB_BRANCH") ||
      props.getProperty("TARGET_BRANCH") ||
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

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    CONTRACT_SPEC_V1: CONTRACT_SPEC_V1,
    utf8ByteLength: utf8ByteLength_,
    saveBoundedRelayState: saveBoundedRelayState_,
    extractYoutubeId: extractYoutubeId_,
    canonicalYoutubeUrl: canonicalYoutubeUrl_,
    normalizeGeminiHandoffReceipt: normalizeGeminiHandoffReceipt_,
    extractReceiptPayload: extractReceiptFromText_,
    computeReceiptDigest: computeCanonicalSha256_,
    scanForbiddenKeys: scanForbiddenKeys_,
    validateReceipt: validateReceipt_,
    renderResearchMarkdown: renderResearchMarkdown_,
    formatRelatedRecordsLines: formatRelatedRecordsLines_,
    renderDeltaSection: renderDeltaSection_,
    extractVideoIdsFromMarkdownText: extractVideoIdsFromMarkdownText_,
    validateLoopStateSchema: validateLoopStateSchema_,
    renderGitHubKnowledgeIndexExportMd: renderGitHubKnowledgeIndexExportMd_,
    planReceiptApplication: planReceiptApplication_,
    relayDriveReceiptsToGitHub: relayDriveReceiptsToGitHub,
    runCloudRelayDryRun: runCloudRelayDryRun,
    runCloudRelayLoop: runCloudRelayLoop,
    runCloudRelayLoop_: runCloudRelayLoop_,
    pullGitHubIndexExportToDriveDoc: pullGitHubIndexExportToDriveDoc,
    syncResearchCardsToDriveSafely: syncResearchCardsToDriveSafely_,
  };
}

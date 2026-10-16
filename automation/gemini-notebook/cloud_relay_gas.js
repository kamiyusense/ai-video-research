/**
 * AI技術研究室 | Gemini Notebook -> Private GitHub Cloud Relay (Google Apps Script v0.3)
 *
 * 目的:
 *   自宅PCの電源がOFFでも、Googleクラウド上でGemini Tasksの研究結果（Google Docsエクスポート / Driveファイル）を
 *   自動検知し、非公開GitHub (`kamiyusense/ai-video-research`) の GitHub Actions (`repository_dispatch`) へ
 *   安全に受け渡す。
 *
 * 安全設計・境界:
 *   1. 追加従量課金ゼロ（Google Apps Script 無料枠・GitHub Actions 無料枠のみ使用）。
 *   2. 送信先は `kamiyusense/ai-video-research` の許可された非defaultブランチのみ（main直接書込み禁止）。
 *   3. 冪等性保証: Receipt JSONの正規化SHA-256ダイジェストを ScriptProperties に記録し、同一Receiptを二度送信しない。
 *   4. retry=0 / Stop-on-unknown-write: GitHub API応答が 204 以外または不明な場合は自動再送せず、
 *      `UNKNOWN_NEEDS_READBACK` として記録・停止する。
 *   5. 索引の厳格な分離: GitHub側から取得する `github_knowledge_index_export.md` は、
 *      Gemini Notebook内の既存総合索引 (`AI技術研究室_知識索引.md`) とは別ドキュメントとして保存し、
 *      Notebook内の既存総合索引を上書き破壊しない。
 *   6. GitHubへの送信成功 (`DISPATCHED_TO_GITHUB`) を、GitHub保存完了やNotebook同期完了と混同しない。
 *
 * 必要なスクリプトプロパティ (Project Settings > Script Properties):
 *   - GITHUB_FINE_GRAINED_PAT : `kamiyusense/ai-video-research` のみ対象、Contents (Read/Write) または Actions/Workflows 権限を持つトークン
 *   - DRIVE_INBOX_FOLDER_ID   : Geminiから「Googleドキュメントにエクスポート」または保存したファイルを置くGoogle DriveフォルダID
 *   - TARGET_GITHUB_BRANCH    : (任意) 既定値 "feature/gemini-notebook-research-loop-20261016"
 *   - DRIVE_EXPORT_DOC_ID     : (任意) GitHub側の `github_knowledge_index_export.md` を反映する専用GoogleドキュメントID
 */

const EXPECTED_REPO_OWNER = "kamiyusense";
const EXPECTED_REPO_NAME = "ai-video-research";
const DEFAULT_TARGET_BRANCH = "feature/gemini-notebook-research-loop-20261016";
const FORBIDDEN_BRANCHES = ["main", "master"];

/**
 * メインエントリ1: Google Drive の Inbox フォルダを走査し、未処理の `research_receipt_v1` を GitHub Actions へ転送する。
 * （時間主導型トリガーで15分〜1時間おき、または手動で実行可能。自宅PCの起動は不要。）
 */
function relayDriveReceiptsToGitHub() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("GITHUB_FINE_GRAINED_PAT");
  const folderId = props.getProperty("DRIVE_INBOX_FOLDER_ID");
  const targetBranch = (props.getProperty("TARGET_GITHUB_BRANCH") || DEFAULT_TARGET_BRANCH).trim();

  if (!token || !folderId) {
    throw new Error("Missing required Script Properties: GITHUB_FINE_GRAINED_PAT and/or DRIVE_INBOX_FOLDER_ID");
  }
  if (!targetBranch || FORBIDDEN_BRANCHES.indexOf(targetBranch) !== -1) {
    throw new Error("Refusing default or empty target branch: " + targetBranch);
  }

  const stateJson = props.getProperty("RELAY_STATE_V1");
  let relayState = { processedDigests: {}, haltedReceipts: {} };
  if (stateJson) {
    try {
      relayState = JSON.parse(stateJson);
      if (!relayState || typeof relayState !== "object" || !relayState.processedDigests) {
        throw new Error("Invalid RELAY_STATE_V1 structure");
      }
    } catch (e) {
      // 既存の状態が破損している場合は無断で初期化せず安全停止する
      throw new Error("Corrupted RELAY_STATE_V1 in ScriptProperties; refusing to reset state: " + e.message);
    }
  }

  const folder = DriveApp.getFolderById(folderId);
  const files = folder.getFiles();
  const report = [];

  while (files.hasNext()) {
    const file = files.next();
    const mime = file.getMimeType();
    const name = file.getName();
    let rawText = "";

    try {
      if (mime === MimeType.GOOGLE_DOCS) {
        rawText = DocumentApp.openById(file.getId()).getBody().getText();
      } else if (
        mime === MimeType.PLAIN_TEXT ||
        name.endsWith(".json") ||
        name.endsWith(".md") ||
        name.endsWith(".txt")
      ) {
        rawText = file.getBlob().getDataAsString("UTF-8");
      } else {
        continue;
      }
    } catch (readErr) {
      report.push({ file: name, status: "READ_ERROR_SKIPPED", detail: String(readErr) });
      continue;
    }

    const receiptObj = extractReceiptFromText_(rawText);
    if (!receiptObj) {
      report.push({ file: name, status: "SKIPPED_NO_RECEIPT" });
      continue;
    }

    const digest = computeCanonicalSha256_(receiptObj);
    if (relayState.processedDigests[digest]) {
      report.push({ file: name, digest: digest, status: "SKIP_DUPLICATE_ALREADY_DISPATCHED" });
      continue;
    }
    if (relayState.haltedReceipts[digest]) {
      report.push({
        file: name,
        digest: digest,
        status: "HALTED_PREVIOUS_UNKNOWN_WRITE_NEEDS_READBACK",
      });
      continue;
    }

    // GitHub Actions `repository_dispatch` へ1回だけ送信 (retry=0)
    const dispatchUrl =
      "https://api.github.com/repos/" +
      EXPECTED_REPO_OWNER +
      "/" +
      EXPECTED_REPO_NAME +
      "/dispatches";
    const payload = {
      event_type: "gemini_research_receipt",
      client_payload: {
        target_branch: targetBranch,
        receipt_sha256: digest,
        source_file_name: name,
        receipt: receiptObj,
      },
    };

    const response = UrlFetchApp.fetch(dispatchUrl, {
      method: "post",
      contentType: "application/json",
      headers: {
        Authorization: "Bearer " + token,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      payload: JSON.stringify(payload),
      muteHttpExceptions: true,
    });

    const code = response.getResponseCode();
    if (code === 204) {
      relayState.processedDigests[digest] = {
        dispatchedAt: new Date().toISOString(),
        sourceFile: name,
        targetBranch: targetBranch,
        githubWriteStatus: "DISPATCHED_TO_GITHUB_ACTIONS_PENDING_RUN",
        notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
      };
      props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));
      report.push({
        file: name,
        digest: digest,
        status: "DISPATCHED_TO_GITHUB_ACTIONS",
        notebookSyncStatus: "NOT_SYNCED_FROM_GITHUB",
      });
    } else {
      // 結果不明またはエラー時は自動再送せず停止記録を残す
      relayState.haltedReceipts[digest] = {
        haltedAt: new Date().toISOString(),
        httpCode: code,
        responseBody: response.getContentText().slice(0, 300),
      };
      props.setProperty("RELAY_STATE_V1", JSON.stringify(relayState));
      report.push({
        file: name,
        digest: digest,
        status: "STOPPED_ON_NON_204_NO_RETRY",
        httpCode: code,
      });
      break;
    }
  }

  Logger.log(JSON.stringify({ relayReport: report }, null, 2));
  return report;
}

/**
 * メインエントリ2 (任意): GitHub非defaultブランチ上の `github_knowledge_index_export.md` を読み取り、
 * Google Drive上の専用Googleドキュメント（Notebook内の既存総合索引 `AI技術研究室_知識索引.md` とは別ファイル）へ反映する。
 */
function pullGitHubIndexExportToDriveDoc() {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("GITHUB_FINE_GRAINED_PAT");
  const exportDocId = props.getProperty("DRIVE_EXPORT_DOC_ID");
  const targetBranch = (props.getProperty("TARGET_GITHUB_BRANCH") || DEFAULT_TARGET_BRANCH).trim();

  if (!token || !exportDocId) {
    throw new Error("Missing GITHUB_FINE_GRAINED_PAT or DRIVE_EXPORT_DOC_ID");
  }

  const path = "automation/gemini-notebook/state/github_knowledge_index_export.md";
  const url =
    "https://api.github.com/repos/" +
    EXPECTED_REPO_OWNER +
    "/" +
    EXPECTED_REPO_NAME +
    "/contents/" +
    encodeURIComponent(path) +
    "?ref=" +
    encodeURIComponent(targetBranch);

  const response = UrlFetchApp.fetch(url, {
    method: "get",
    headers: {
      Authorization: "Bearer " + token,
      Accept: "application/vnd.github.raw+json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    muteHttpExceptions: true,
  });

  if (response.getResponseCode() !== 200) {
    throw new Error("Failed to fetch github_knowledge_index_export.md: HTTP " + response.getResponseCode());
  }

  const markdownText = response.getContentText("UTF-8");
  const doc = DocumentApp.openById(exportDocId);
  const docTitle = doc.getName();

  // 安全境界: Notebook内の既存総合索引と同名のドキュメントへの上書きを拒否する
  if (docTitle.indexOf("AI技術研究室_知識索引") !== -1) {
    throw new Error(
      "Refusing to overwrite Notebook master index document ('AI技術研究室_知識索引'). Use a separate Google Doc for GitHub export."
    );
  }

  doc.getBody().setText(markdownText);
  doc.saveAndClose();

  const result = {
    status: "DRIVE_EXPORT_DOC_UPDATED",
    docId: exportDocId,
    docTitle: docTitle,
    sourceBranch: targetBranch,
    notebookMasterIndexOverwritten: false,
    notebookSyncStatus: "DRIVE_DOC_UPDATED_NOTEBOOK_RESYNC_SEPARATE",
  };
  Logger.log(JSON.stringify(result, null, 2));
  return result;
}

/**
 * テキストまたはMarkdownコードブロックから `research_receipt_v1` オブジェクトを抽出する内部関数
 */
function extractReceiptFromText_(rawText) {
  if (!rawText || typeof rawText !== "string") return null;
  const trimmed = rawText.trim();
  if (trimmed.startsWith("{")) {
    try {
      const obj = JSON.parse(trimmed);
      if (obj && obj.schema_version === "research_receipt_v1") return obj;
    } catch (e) {}
  }
  const fenceRegex = /```(?:json)?\s*(\{[\s\S]*?\})\s*```/gi;
  let match;
  while ((match = fenceRegex.exec(rawText)) !== null) {
    try {
      const obj = JSON.parse(match[1].trim());
      if (obj && obj.schema_version === "research_receipt_v1") return obj;
    } catch (e) {}
  }
  return null;
}

/**
 * オブジェクトのキーを再帰的にソートして決定論的なSHA-256（16進文字列）を計算する内部関数
 */
function computeCanonicalSha256_(obj) {
  const canonicalJson = canonicalizeJson_(obj);
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

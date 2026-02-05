# Design Rules

## Payload 傳遞規則

**Rule 1**: 所有層級統一使用 handle_payload

從 router 開始構建 handle_payload，一路傳遞到最底層。

**Rule 2**: 保持 payload 完整性，不提取、不拆解

- ✅ 正確：module.process(handle_payload)
- ❌ 錯誤：module.process(prompt) ← 資訊丟失

## 職責分離規則

**Rule 3**: Utility 專注單一功能（純函數）

Utility 函數只做一件事，不混合職責：
- match()：只負責條件匹配
- action_deny()：只負責拒絕動作
- transform_input()：只負責輸入轉換

**Rule 4**: Handle 是工作流編排（Workflow Orchestrator）

Handle 不實現具體邏輯，是工作流編排者：
- 編排執行順序（match → action → feature → output）
- 調用 utility 執行單一功能
- 調用 module 執行業務邏輯
- 整合結果返回

**Rule 5**: Module 實現業務邏輯

Module 接收完整 payload，自主決定處理方式：
- 可以返回 HookResult（完全控制）
- 可以返回 str（簡單 context）
- 可以返回 None（僅副作用）

## 命名規範

**Rule 6**: 使用官方欄位名（camelCase → snake_case → camelCase）

- Rule 配置：官方 camelCase（updatedInput, additionalContext）
- Python 變數：snake_case（updated_input, additional_context）
- 最終 JSON：官方 camelCase

**Rule 7**: Payload 層級命名

- handle_payload: Handler 層統一格式
- feature_payload: Feature 層（= handle_payload）
- claude_payload: 原始官方 payload（handle_payload['claude']）

## 錯誤處理規則

**Rule 8**: 錯誤返回 HookResult(additional_context="⚠️ 錯誤")

執行錯誤時返回 context，不中斷流程。

**Rule 9**: 單一 rule 錯誤不阻斷其他 rule

單一 rule 錯誤不影響其他 rule 執行（並發隔離）。

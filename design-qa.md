# Design QA — Login redesign, selected option 2

- Source visual truth: `C:\home\github\child_presence_detection\tmp\design-qa\source-option-2.png`
- Implementation screenshot: `C:\home\github\child_presence_detection\tmp\design-qa\implementation-option-2-final.png`
- Final combined comparison: `C:\home\github\child_presence_detection\tmp\design-qa\comparison-final.png`
- Viewport: 1280 × 720 CSS px
- Source pixels: 1672 × 941
- Implementation pixels: 1280 × 720
- Density normalization: implementation screenshot pixels match the CSS viewport at 1:1. For direct comparison, both images were aspect-fit into equal 760 × 427 frames; no device frame or browser chrome was included.
- State: logged out, recovery panel collapsed, empty Staff ID and PIN fields.

## Findings

No actionable P0, P1, or P2 differences remain.

- Fonts and typography: system UI / Noto Sans JP-style fallbacks, weight hierarchy, heading tracking, label scale, and wrapping are visually aligned with the source. The source image is generated raster text, so minor antialiasing differences are expected.
- Spacing and layout rhythm: header height, divider position, centered headline, three-step guide, form rhythm, action height, and recovery-link placement align after the second visual pass. The implementation form column is approximately 2–3% narrower than the raster source; this is accepted as P3 because it preserves the intended 560px app surface and improves stable responsive padding.
- Colors and visual tokens: off-white page, white app surface, deep forest text, muted teal action, gray-green borders, and low-elevation treatment match the source direction with accessible contrast.
- Image quality and asset fidelity: the selected screen contains no logos, illustrations, photos, or non-standard icons. No raster assets, emoji, handcrafted SVGs, or placeholders were substituted. The progress indicator is a native UI component rendered in CSS.
- Copy and content: all visible source copy is preserved exactly: `送迎バス安全確認`, `まもるバス`, `確認を、ひとつずつ。`, `乗車`, `降車`, `車内確認`, `職員ID`, `PIN`, `ログイン`, and `管理者PINを復旧する`.

## Full-view comparison evidence

`tmp/design-qa/comparison-final.png` places the selected option and the browser-rendered implementation in the same normalized comparison image. Major proportions, vertical landmarks, form geometry, action prominence, and whitespace are visibly aligned.

## Focused region evidence

A separate crop was not required: the equal-size 760 × 427 comparison keeps the header, progress guide, form labels, inputs, button, and recovery link readable. Browser-computed measurements additionally confirmed a 560 × 720 app surface, 58px input heights, and an 80px primary action.

## Interaction and browser checks

- Staff ID and PIN inputs accepted and cleared test values.
- The recovery control expanded and collapsed the recovery panel.
- The recovery panel exposed labeled token and new-PIN fields plus the expected disabled submit state.
- Console warnings/errors checked: none.
- Production build: passed.
- Responsive CSS is present for widths up to 560px. The in-app browser kept its 1280 × 720 viewport despite the temporary 390 × 844 override request, so a separate browser-rendered mobile screenshot remains a non-blocking P3 test gap; the selected source and acceptance viewport are desktop.

## Comparison history

1. Initial browser pass: found a P2 mismatch in primary-action height and recovery-link spacing. The implementation used a 64px button while the selected source visually resolved to approximately 80px at the normalized viewport.
2. Fix: increased the primary action to 80px and recovery spacing to 30px.
3. Intermediate browser pass: the larger action introduced a P2 4px vertical overflow and visible scrollbar at 1280 × 720.
4. Fix: reduced login-main bottom padding by 8px.
5. Final browser pass: scroll height equals viewport height (720px), no scrollbar, no console errors, and no actionable P0/P1/P2 differences remain.

## Follow-up polish

- P3: capture a dedicated 390 × 844 browser screenshot when the in-app viewport override is available.

final result: passed
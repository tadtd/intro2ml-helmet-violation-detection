# Slides

Slide chính của report nằm ở `slide/main.tex`.

## Cấu trúc

- `main.tex`: entry point của Beamer deck.
- `content/slides.tex`: index `\input` các section.
- `content/01_*.tex` đến `content/06_*.tex`: nội dung từng section của slide.
- `theme/`: theme Beamer local `SimpleDarkBlue`.
- `img/`: hình dùng trong slide report.
- `ref/`: BibTeX tham khảo nếu cần mở rộng citation.

## Compile

Slide được cấu hình để compile on save bằng extension VS Code LaTeX Workshop của James Yu.

Mở `slide/main.tex` trong VS Code và lưu file để extension tự build theo cấu hình LaTeX Workshop hiện có.

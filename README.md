# Hệ thống Sinh Map Tự động (Map Generation System)

Dự án này được thiết kế để tự động sinh ra các map game 3D dựa trên các khái niệm lập trình cần dạy.

## Cấu trúc Thư mục

- `data/`: Chứa dữ liệu đầu vào (curriculum) và đầu ra (generated maps).
- `src/`: Chứa toàn bộ mã nguồn của hệ thống.
- `scripts/`: Chứa các script để thực thi các tác vụ, ví dụ như sinh tất cả các map.
- `tests/`: Chứa các bài kiểm thử tự động.

## Cách chạy

1.  Tạo và kích hoạt môi trường ảo:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
2.  Cài đặt các thư viện:
    ```bash
    pip install -r requirements.txt
    ```
3.  Chạy script sinh map:
    ```bash
    python3 -m scripts.generate_all_maps
    ```
FROM python:3.11-slim

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Sao chép mã nguồn và cấu hình
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY . .

# Chạy bot ở chế độ tương tác 24/7 kết hợp tự động lên lịch 07:00 AM
CMD ["uv", "run", "python", "-m", "src.interactive_bot"]

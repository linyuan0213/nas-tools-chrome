# Nas-tools Chrome Server

### 运行方式

  - 直接安装

    ```sh
    pip install -r requirements.txt

    uvicorn app:app --host 0.0.0.0 --port 9850
    ```

  - 通过 docker 部署

    ```
    docker run -p 9850:9850 -d linyuan213/nas-tools-chrome:latest
    ```


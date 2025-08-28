# Hướng dẫn chạy MongoDB với Replica Set (rs0)

## 1. Yêu cầu
- Đã cài đặt Docker và Docker Compose
- Đã có file `docker_compose.yml` như sau:

```yaml
services:
  mongo:
    image: mongo:6.0
    container_name: mongodb
    command: ["mongod", "--replSet", "rs0", "--bind_ip_all"]
    ports:
      - "27017:27017"
    volumes:
      - ./mongo-data:/data/db
      - ./init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
```

## 2. Khởi động MongoDB với Docker Compose

```sh
docker compose -f docker_compose.yml up -d
```

## 3. Khởi tạo Replica Set
Sau khi container MongoDB đã chạy, bạn cần khởi tạo replica set:

```sh
docker exec -it mongodb mongosh
```

Trong shell MongoDB, chạy lệnh sau:
```js
rs.initiate()
```

Nếu thành công, bạn sẽ thấy trạng thái replica set đã được khởi tạo.

## 4. Kiểm tra trạng thái Replica Set
```js
rs.status()
```

## 5. Kết nối từ ứng dụng
Sử dụng connection string:
```
mongodb://localhost:27017/?replicaSet=rs0
```

## 6. Lưu ý
- Nếu dùng file `init-mongo.js` để khởi tạo dữ liệu, hãy đảm bảo file này nằm đúng vị trí và có quyền đọc.
- Replica set cần thiết cho các tính năng transaction của MongoDB.

---
**Tham khảo:**
- [MongoDB Docker Official](https://hub.docker.com/_/mongo)
- [MongoDB Replica Set Docs](https://www.mongodb.com/docs/manual/replication/)

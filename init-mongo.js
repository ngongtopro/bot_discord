// Tự động khởi tạo replica set khi container start
rs.initiate(
  {
    _id: "rs0",
    members: [
      { _id: 0, host: "localhost:27017" }
    ]
  }
)

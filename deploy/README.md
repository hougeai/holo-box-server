# 构建前端容器命令
```
# 需要在项目根目录运行Docker构建命令，并在根目录指定dockerignore文件

docker build --no-cache -f docker/Dockerfile.frontend --build-arg VITE_BASE_URL=http://42.193.183.35:3000/api/v1 --build-arg VITE_OSS_BUCKET_URL=https://objectstorageapi.bja.sealos.run/holo-box -t holobox-frontend:v1.0 .

# 运行容器并映射端口
docker run -d --name xzp-fe -p 8078:8078 holobox-frontend:v1.0
```

# 构建后端容器命令
```
# 运行Docker构建命令
docker build -f docker/Dockerfile.backend -t holobox-backend:v1.0 .
# 运行后端容器命令，环境变量.env中不能用"'引号
docker run -d -p 3002:3002 --name xzp-be --env-file backend/app/.env holobox-backend:v1.0
# 进入容器查看
docker exec -it xzp-be /bin/bash
```

# 上传/下载镜像
```
docker login --username=actionlw registry.cn-shanghai.aliyuncs.com
docker tag 2b679e5b7027 registry.cn-shanghai.aliyuncs.com/hougeai/holobox-frontend:v1.0
docker push registry.cn-shanghai.aliyuncs.com/hougeai/holobox-frontend:v1.0
docker pull registry.cn-shanghai.aliyuncs.com/hougeai/holobox-frontend:v1.0
```

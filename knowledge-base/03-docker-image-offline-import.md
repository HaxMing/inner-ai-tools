# Docker 镜像离线导入

## 文档用途

本文记录在内网或弱网环境中离线导入 Docker 镜像的方法。适合回答：

```text
服务器不能联网怎么导入镜像？
docker save 和 docker load 怎么用？
Dify 镜像怎么离线迁移？
导入镜像后 docker compose 还是拉取失败怎么办？
```

## 基本概念

Docker 镜像离线迁移通常分为三步：

```text
1. 在有网络的机器上拉取镜像。
2. 使用 docker save 导出为 tar 文件。
3. 拷贝到内网服务器后使用 docker load 导入。
```

常用命令：

```bash
docker pull IMAGE:TAG
docker save -o image-name.tar IMAGE:TAG
docker load -i image-name.tar
docker images | grep IMAGE
```

## 导出镜像

在有网络的机器执行：

```bash
docker pull nginx:latest
docker save -o nginx-latest.tar nginx:latest
```

导出多个镜像：

```bash
docker save -o dify-images.tar image1:tag image2:tag image3:tag
```

如果镜像很多，建议按服务分类导出：

```text
dify-core-images.tar
dify-db-images.tar
dify-plugin-images.tar
model-service-images.tar
```

## 传输到内网服务器

从 Windows 传到 Linux 服务器：

```powershell
scp .\nginx-latest.tar root@192.168.1.102:/tmp/
```

从 Linux 传到 Linux：

```bash
scp nginx-latest.tar root@192.168.1.102:/tmp/
```

如果文件很大，建议校验哈希：

```bash
sha256sum nginx-latest.tar
```

传输后在目标服务器再次执行：

```bash
sha256sum /tmp/nginx-latest.tar
```

两边结果一致才说明文件未损坏。

## 导入镜像

在目标服务器执行：

```bash
docker load -i /tmp/nginx-latest.tar
```

查看导入结果：

```bash
docker images | grep nginx
```

如果镜像标签不符合 docker-compose.yml，需要重新打标签：

```bash
docker tag old-image:old-tag new-image:new-tag
```

## 配合 docker compose 使用

进入 compose 目录：

```bash
cd /wtq/dify/dify-1.14.2/docker
```

先查看 compose 需要哪些镜像：

```bash
docker compose config | grep image:
```

确认本地已有镜像：

```bash
docker images
```

启动：

```bash
docker compose up -d
```

如果仍然尝试联网拉取镜像，说明本地镜像名或 tag 与 compose 文件不一致。

## 常见错误

### no such image

原因：

```text
docker-compose.yml 需要的镜像名和本地导入的镜像名不一致。
```

解决：

```bash
docker compose config | grep image:
docker images
docker tag 本地镜像名:本地tag compose需要的镜像名:compose需要的tag
```

### archive/tar: invalid tar header

原因：

```text
tar 文件损坏、传输不完整，或文件不是 docker save 生成的镜像包。
```

解决：

```bash
ls -lh image.tar
sha256sum image.tar
docker load -i image.tar
```

### requested access to the resource is denied

原因：

```text
docker compose 仍在尝试从远程 registry 拉取镜像，且没有权限。
```

解决：

```text
确认本地镜像 tag 和 compose 文件完全一致。
```

## 风险提醒

以下操作有风险：

```bash
docker image prune -a
docker system prune -a
docker rmi ...
```

这些命令会删除镜像，可能导致容器无法重新启动。执行前必须确认：

```text
1. 当前容器是否正在使用该镜像。
2. 是否有离线镜像备份。
3. 是否能重新导入。
```

## 验证命令

```bash
docker images
docker compose config | grep image:
docker compose ps
```

## 推荐问法

```text
我有一个 xxx.tar 镜像包，怎么导入到 192.168.1.102？
docker load 后 compose 还是拉取镜像怎么办？
怎么确认 Dify 所需镜像都已经离线导入？
```

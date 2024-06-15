# py-utils

docker run -e AWS_BUCKET_NAME=your-bucket-name -e AWS_ACCESS_KEY_ID=your-access-key-id -e AWS_SECRET_ACCESS_KEY=your-secret-access-key algostonk:py-utils --verify backup C:/Users/Aditya/Projects/Algostonk/knowledge_base/data/knowledge

docker run -it -e AWS_BUCKET_NAME=kb-backups -e AWS_ACCESS_KEY_ID=<> -e AWS_SECRET_ACCESS_KEY=<> -v ../knowledge_base/data:/data algostonk:py-utils "--verify" "backup" "/data" "knowledge"
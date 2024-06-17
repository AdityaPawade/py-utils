# py-utils

docker build --platform linux/amd64 -t algostonk:py-utils-amd64 .
docker build --platform linux/arm64 -t algostonk:py-utils-arm64 .

docker run -it -e AWS_BUCKET_NAME=kb-backups -e AWS_ACCESS_KEY_ID=<> -e AWS_SECRET_ACCESS_KEY=<> -v ${KB_HOME}/data:/data algostonk:py-utils "--verify" "backup" "/data" "knowledge"

docker image tag algostonk:py-utils-amd64 adtsw/prod:algostonk-py-utils-amd64
docker image tag algostonk:py-utils-arm64 adtsw/prod:algostonk-py-utils-arm64

docker push adtsw/prod:algostonk-py-utils-amd64
docker push adtsw/prod:algostonk-py-utils-arm64

## Commands
python /app/backup_manager.py restore /data knowledge
/usr/local/bin/python /usr/local/bin/sqlite_web /data/knowledge/db/kb.db -p 17434 -H 0.0.0.0
/usr/local/bin/python /usr/local/bin/sqlite_web -r /data/knowledge/db/kb.db -p 17434 -H 0.0.0.0
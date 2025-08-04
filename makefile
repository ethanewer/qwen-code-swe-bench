run:
	uv run swebench.py \
		--subset verified \
		--split test \
		--workers 16 \
		--slice 0:1 \
		--config swebench.yaml \
		--output output
clean:
	rm -rf output

build-docker:
	docker buildx build --load --platform=linux/amd64 --progress=plain --build-arg BASE_IMG=swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest --build-arg CACHEBUST=$(date +%s) -f /Users/ethanewer/swe-agent-test/docker/DockerFile.custom-agent -t swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest-custom-agent /Users/ethanewer/swe-agent-test/docker

run-docker:
	docker run --rm -it --platform linux/amd64 --entrypoint /bin/sh swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest-custom-agent
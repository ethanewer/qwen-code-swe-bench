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
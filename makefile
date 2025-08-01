run:
	uv run swebench.py \
		--subset verified \
		--split test \
		--workers 16 \
		--slice 2:3 \
		--config swebench.yaml \
		--output output
clean:
	rm -r output
run:
	uv run swebench.py \
		--subset verified \
		--split test \
		--workers 16 \
		--slice 1:2 \
		--config swebench.yaml \
		--output output
clean:
	rm -r output
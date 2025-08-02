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

no:
	uv run swebench.py \
		--model gpt-4.1 \
		--subset verified \
		--split test \
		--workers 16 \
		--slice 1:2 \
		--output output
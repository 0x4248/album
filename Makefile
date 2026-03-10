PYTHON ?= python3
ROOT ?= imgs
MAX_KB ?= 500
MIN_KB ?= 200
LOG_EVERY ?= 10

.PHONY: help import dry-run compress-all compress-all-hq

help:
	@echo "Album workflow targets:"
	@echo "  make import                # interactive import from 0_INSERT_HERE"
	@echo "  make dry-run               # preview full compression on $(ROOT)"
	@echo "  make compress-all          # write-mode full compression on $(ROOT)"
	@echo "  make compress-all-hq       # write-mode full compression with better color"
	@echo ""
	@echo "Override defaults like:"
	@echo "  make dry-run ROOT=imgs/2025/06 MAX_KB=500 MIN_KB=200 LOG_EVERY=10"

import:
	$(PYTHON) import_and_sort.py

dry-run:
	$(PYTHON) compress_full_imgs.py \
		--root $(ROOT) \
		--max-kb $(MAX_KB) \
		--min-kb $(MIN_KB) \
		--log-every $(LOG_EVERY) \
		--dry-run

compress-all:
	$(PYTHON) compress_full_imgs.py \
		--root $(ROOT) \
		--max-kb $(MAX_KB) \
		--min-kb $(MIN_KB) \
		--log-every $(LOG_EVERY)

compress-all-hq:
	$(PYTHON) compress_full_imgs.py \
		--root $(ROOT) \
		--max-kb $(MAX_KB) \
		--min-kb $(MIN_KB) \
		--jpeg-subsampling 0 \
		--log-every $(LOG_EVERY)

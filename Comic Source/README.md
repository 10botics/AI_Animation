# Comic Source

Drop each manga chapter you work on in its **own subfolder** here.

## Layout

```
Comic Source/
├── Chapter-81/
│   ├── 001.jpg … 016.jpg
│   ├── stage_01_ingest.md
│   ├── stage_02_shot_list.md
│   └── stage_03_series_bible.md
└── Chapter-82/          ← add the next chapter the same way
    ├── …
    └── stage_02_shot_list.md   ← required for the dashboard to find it
```

The **AI Animation Studio** dashboard scans the **whole project** for chapter folders (any path that contains **`stage_02_shot_list.md`**). Recommended location is here under `Comic Source/`; legacy root folders like `Chapter-81/` or mentor test packs are picked up too.

## Mentor pack

Extract the mentor ZIP so **`Chapter-81/`** lands here:

`Comic Source/Chapter-81/`

Each chapter folder must contain **`stage_02_shot_list.md`** — that is how scripts and the dashboard know the folder is valid.

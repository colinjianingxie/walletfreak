# Manual Card Data Seeding Workflow

This guide details how to manually update credit card data using the "Grok" prompt generation workflow. This is useful when you want to review the data before it enters the system or if you are running in a constrained environment.

## Workflow

### 1. Generate Prompt
Run the following command to generate a structured prompt for the specific card you want to update. This will write the prompt to `card_updates.json` in the project root.

```bash
python manage.py update_cards_grok --cards [card-slug] --prompt
```

*Replace `[card-slug]` with the actual slug of the card (e.g., `the-world-of-hyatt-credit-card`).*

### 2. Manual LLM Interaction
1. Open the file `card_updates.json` (located in the project root, or `../card_updates.json` relative to `manage.py`).
2. Copy the entire content of the file.
3. Paste the content into an LLM (e.g., Grok, ChatGPT, Claude).
4. Copy the **JSON output** provided by the LLM.
5. Paste the JSON output back into `card_updates.json`, completely overwriting the previous content. Ensure it is valid JSON.

### 3. Ingest Data
Run the ingestion script to process the JSON file. This separates the data into the correct relational files (header, benefits, rates, etc.) and handles versioning.

```bash
python manage.py ingest_card_json
```

### 4. Seed Database
Finally, seed the database with the newly updated card data to make it live in the application.

```bash
python manage.py seed_db --cards [card-slug]
```

*Replace `[card-slug]` with the same slug used in step 1.*

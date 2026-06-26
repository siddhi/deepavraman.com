---
name: article-import-assistant
description: Imports a local HTML article into a Pelican website as an .rst file. Use this for importing and formatting articles for the blog.
---

# Skill: Website Article Import Assistant

## Purpose

This skill imports a locally saved HTML article into my Pelican website.

The goal is to convert a saved HTML article into a Pelican-compatible `.rst` article.

Never modify any project files until I explicitly approve each step.

---

# Workflow

## Step 1 — Read the Article

The user will provide the location of a local HTML file.

Example:

```
C:\Users\Hari\Downloads\intern\hindu\Meet Raghavasimhan Sankaranarayanan's robotic violinist that plays Carnatic music.html
```

Read the HTML file.

Extract only the main article.

Ignore:

* navigation
* sidebar
* footer
* advertisements
* cookie banners
* videos
* unrelated links

Do not summarize or rewrite the article during this step.

After successfully extracting the article, ask:

```
I have successfully extracted the article.

Would you like me to validate the extracted content?

Reply:

YES — Continue

NO — Stop
```

Wait for my response.

Never continue automatically.

---

## Step 2 — Validate the Extracted Article

Verify that the extracted article contains sufficient meaningful content.

If the extracted content contains:

* no article body
* only navigation
* only advertisements
* only images
* corrupted HTML
* empty content
* insufficient meaningful text

Stop immediately.

Display:

```
I couldn't extract enough article content from the provided HTML file.

Possible reasons:

- The wrong HTML file was selected.
- The page was not saved correctly.
- The article requires JavaScript to load.
- The HTML file is incomplete or corrupted.

Please provide another HTML file.
```

Wait for the user.

Do not continue.

Do not generate:

* title
* summary
* metadata
* article

Do not modify any project files.

If the article is valid, display:

```
The article has been successfully validated.

Would you like me to generate a title?

YES — Continue

NO — Stop
```

Wait for approval.

---

## Step 3 — Generate the Title

Generate one concise, descriptive, SEO-friendly title.

Requirements:

* represent the article accurately
* avoid clickbait
* preserve names where appropriate
* use title case where appropriate

Display only the proposed title.

Ask:

```
Is this title OK?

YES — Continue

NO — Generate another title
```

Wait for approval.

Do not continue until the title is approved.

---

## Step 4 — Summarize the Article

Create a blog-ready summary.

Requirements:

* preserve all important facts
* remove repetition
* maintain factual accuracy
* do not add opinions
* do not invent information
* keep the author's meaning
* produce a concise summary suitable for the `:summary:` metadata field and introductory section

Display only the summary.

Ask:

```
Is this summary OK?

YES — Continue

NO — Tell me what should change
```

Wait for approval.

---

## Step 5 — Generate Metadata

Generate the following metadata:

* Title
* Date (today unless specified otherwise)
* Category
* Tags
* Slug
* Summary
* Suggested filename
* Estimated reading time

Display the metadata.

Ask:

```
Is this metadata OK?

YES — Continue

NO — Tell me what to change
```

Wait for approval.

---

## Step 6 — Generate the Complete Pelican Article

Generate a complete Pelican-compatible `.rst` article.

Use the following structure:

```
Title
=======================================================================================

:date:
:category:
:tags:
:summary:

Article content...
```

Requirements:

* preserve article meaning
* preserve interview format if applicable
* preserve quotations
* preserve image references if available
* use valid reStructuredText syntax
* do not invent facts
* do not add new sections unrelated to the article

Display the complete article.

Ask:

```
Is the complete article OK?

YES — Write it to the project

NO — Tell me what should change
```

Wait for approval.

---

## Step 7 — Create the Article

Only after receiving explicit approval:

Locate the `content/` directory.

Create a new `.rst` file using the approved filename.

If the filename already exists:

append

```
-2
-3
-4
```

until a unique filename is found.

Never overwrite an existing article.

Report:

```
Created:

content/<filename>.rst
```

Do not modify:

* output/
* generated HTML
* generated CSS

Do not run any build commands.

---

## Step 8 — Ask Before Running

After successfully creating the article, ask:

```
The article has been created successfully.

Would you like me to run the website build command to preview the changes?

YES — Run the appropriate build command.

NO — Finish without running anything.
```

Wait for my response.

Never run any command without permission.

---

# Safety Rules

* Never modify any files before approval.
* Never overwrite existing articles.
* Never modify the `output/` directory.
* Never generate HTML manually.
* Never skip an approval step.
* Always pause after every major step.
* Never invent information that is not present in the article.
* If required information is missing, ask the user before continuing.
* If the article cannot be extracted, stop the workflow and request another HTML file.
* Never run build commands without explicit approval.
* Never assume file locations; always use the HTML file path provided by the user.

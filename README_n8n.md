# Setup NVIDIA Telegram Image Generator in n8n

You can easily build this bot inside n8n without writing any server code. This directory contains a pre-built workflow JSON file: **[n8n_workflow.json](file:///d:/github%20projects/telegram%20chat%20bot%20(image)/n8n_workflow.json)**.

---

## Step-by-Step Setup Instructions

### 1. Import the Workflow into n8n
1. Open your n8n workspace dashboard.
2. Click on **Workflows** in the sidebar.
3. Click the **+ Add Workflow** button (or open a blank workflow).
4. Click the **three dots menu** (top-right corner of the canvas) and select **Import from File**.
5. Select the **[n8n_workflow.json](file:///d:/github%20projects/telegram%20chat%20bot%20(image)/n8n_workflow.json)** file from this folder.
6. Alternatively, you can open `n8n_workflow.json` in a text editor, copy all of the text (`Ctrl+A` then `Ctrl+C`), and click anywhere on your empty n8n canvas and press **`Ctrl+V` (or `Cmd+V`)**. n8n will automatically parse and draw the entire workflow!

---

### 2. Configure Node Credentials

#### A. Telegram Trigger & Telegram Send Photo Nodes
1. Click on the **Telegram Trigger** node.
2. Under **Credential for Telegram API**, select or add a new Telegram credential.
3. Enter your **Telegram Bot Token**: `8864627308:AAGNRS5miLZzH2F7zDqyPeJbm1BwLhKlHO8`
4. Click Save.
5. Click on the **Telegram Send Photo** node (the last node in the flow) and make sure it uses the same Telegram credential you just added.

#### B. NVIDIA API Call Node
1. Click on the **NVIDIA API Call** node.
2. Look at the **Headers** parameters.
3. Locate the `Authorization` header parameter.
4. Replace `YOUR_NVIDIA_API_KEY_HERE` with your actual NVIDIA developer key:
   `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`
5. The header value should look like this:
   `Bearer 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`

---

### 3. Deploy/Activate the Workflow
1. Click the **Test Step / Listen for Test Event** on the Telegram Trigger node (or click the main **Test Workflow** button at the bottom of the canvas) to test it.
2. Message your bot on Telegram: send a prompt like `sun rise` or `/generate a sunset`.
3. Verify that the workflow triggers, the nodes light up green, and the bot sends back the image.
4. Once verified, turn the **Active** switch at the top-right corner of your n8n workflow canvas to **ON** to deploy it!

---

## How the n8n Workflow Works
1. **Telegram Trigger:** Listens to incoming text messages sent to your Telegram bot.
2. **Extract Prompt & Filter:** Runs a short Javascript snippet that:
   - Validates if the message is in a group or private DM.
   - If in a group, extracts the prompt only when the message starts with `/generate`, `/gen`, or mentions the bot.
   - If in private DM, uses the plain text directly as the prompt.
3. **Filter Trigger:** Checks if we should proceed (ignoring random chat text in groups).
4. **NVIDIA API Call:** Makes a `POST` request to NVIDIA's FLUX.1-schnell endpoint using your API key.
5. **Convert Base64 to Binary:** Takes the base64-encoded image from NVIDIA's JSON response and converts it into a standard image file buffer.
6. **Telegram Send Photo:** Sends the converted image back to the same chat/group, replying directly to the user's prompt.

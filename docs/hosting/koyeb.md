# Deploying Geralt on Koyeb

This guide explains how to run the Geralt Discord bot on [Koyeb](https://www.koyeb.com/) using the repository as the service source. Koyeb's serverless platform automatically builds the project from this repository and keeps it running so the bot is always online.

## Prerequisites

Before you create the Koyeb service, make sure you have:

- A Koyeb account connected to the GitHub repository that hosts your Geralt fork.
- A PostgreSQL database that the bot can reach from Koyeb. You can use Koyeb's managed PostgreSQL add-on or any publicly reachable PostgreSQL provider. Keep the full connection URI handy.
- All secrets required by the bot. The provided [`example_config.env`](../../example_config.env) lists every configuration key the bot can consume.【F:example_config.env†L1-L41】 At minimum you must provide:
  - `TOKEN`: the Discord bot token.
  - `DB_URL`: the PostgreSQL connection string.
  - Any webhook IDs and tokens your deployment relies on (for example the notification, error, and feedback webhooks).
  - Optional tokens for search integrations and GitHub automation, if you intend to use those features.

## Repository layout refresher

Koyeb detects Python projects automatically when a `requirements.txt` file is present in the repository root, which matches this project layout.【F:requirements.txt†L1-L39】 The bot is started by running `python launcher.py`, which simply imports the bot package and launches the asynchronous runner.【F:launcher.py†L1-L9】

## Step-by-step deployment

1. **Prepare the database**  
   Create the PostgreSQL database and restore the schema/data from the `db` backup if needed. Verify that the role referenced in your `DB_URL` has permission to read and write to every table the bot uses.

2. **Create a new application in Koyeb**  
   - Sign in to the Koyeb control panel and click **Create App**.
   - Choose **GitHub** as the deployment source and select the repository and branch you want to deploy.
   - Pick a region close to your Discord guild members to minimize latency.

3. **Configure the build and runtime**  
   - Leave the build preset set to **Auto-detect**. Koyeb will install the dependencies from `requirements.txt` using its Python buildpack.
   - Set the run command to `python launcher.py` so the service starts the bot process.

4. **Add environment variables**  
   - In the **Environment variables** section, add each key/value required by your deployment. Use the secrets you collected in the prerequisites section.  
   - When possible, store long-lived credentials (like the Discord token or database password) as **Secrets** in Koyeb and reference them from the service instead of pasting them inline.

5. **Scale and deploy**  
   - Keep the default instance size unless you know you need more memory or CPU for your workload.  
   - Click **Deploy**. Koyeb will build the image, provision an instance, and start the bot automatically. Subsequent pushes to the selected branch will trigger new deployments.

## Post-deployment management

- **Monitoring**: Use Koyeb's live logs to confirm that the bot connects to Discord successfully and that database migrations (if any) complete without errors. Investigate any connection failures immediately—most issues stem from missing environment variables or incorrect database URIs.
- **Secrets rotation**: When rotating tokens, update the Koyeb secret first, then redeploy the service to pick up the new value. Avoid redeploying with outdated secrets to prevent downtime.
- **Scaling**: If the bot becomes resource-constrained, scale vertically by choosing a larger instance size or horizontally by enabling additional instances. Remember that Discord bots cannot process the same gateway connection from multiple instances unless you configure sharding—ensure your sharding strategy matches the number of instances you run.
- **Updating code**: Push changes to the tracked branch to trigger new deployments. If you need to roll back, redeploy a previous commit from the Koyeb dashboard.

Following these steps will give you a continuously running Geralt instance backed by Koyeb's platform, with manageable secrets and straightforward updates.

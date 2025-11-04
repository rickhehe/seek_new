# SEEK NEW

You-Know-Where Data Engineer Job Tracker

simply run `./run.sh` or
- Get new listings for the 24 hours (customizable)
- Send Telegram notifications for job listings started within the last 10 minutes (customizable)

Feel free to `crontab -e` to schedule periodic runs, e.g., every 10 minutes:
```
*/10 * * * * /path/to/your/project/run.sh
```

In future, I may add visualizations and dashboards using tools like streamlit to analyze job market trends.
# SEEK NEW

New listing tracker on you-know-where (popular job site in AU and NZ). I use it to track Data Engineer jobs.

simply run `./run.sh` to:
- Get new listings
- Save new listings to a PostgreSQL database  
- Send Telegram notifications for new job listings which are not yet in database

Feel free to `crontab -e` to schedule periodic runs, e.g., every 5 minutes:
```
*/5 * * * * /path/to/your/project/run.sh
```

## Future Enhancements

- Visualizations and dashboards using tools like streamlit to analyze job market trends
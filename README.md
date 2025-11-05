# SEEK NEW

New listing tracker on you-know-where (popular job site in AU and NZ). I use it to track Data Engineer jobs.

simply run `./run.sh` or
- Get new listings for the 24 hours (customizable)
- Send Telegram notifications for new job listings (not yet in database)

Feel free to `crontab -e` to schedule periodic runs, e.g., every 10 minutes:
```
*/10 * * * * /path/to/your/project/run.sh
```

## Future Enhancements

- Visualizations and dashboards using tools like streamlit to analyze job market trends
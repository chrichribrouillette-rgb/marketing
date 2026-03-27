Generate marketing content using the industry-specific AI agent.

**Usage:** `/marketing <industry_number> "<your request>" [--brand "<brand context>"]`

**Industries:**
| # | Industry |
|---|----------|
| 1 | Fashion B2C |
| 2 | Beauty B2C |
| 3 | Self-Development & Coaching |
| 4 | B2B Manufacturing |
| 5 | Food & Beverage |
| 6 | Health & Wellness |
| 7 | Travel & Hospitality |
| 8 | Real Estate |
| 9 | Finance & Fintech |
| 10 | Education & EdTech |

**Examples:**
- `/marketing 1 "Write an Instagram caption for our summer drop"`
- `/marketing 2 "Write a launch email for our new serum" --brand "Glossier, minimalist skincare"`
- `/marketing 3 "Write a LinkedIn post for our 8-week coaching programme"`
- `/marketing --list` to see all industries

Run the following command and show the user the result:

```bash
cd /home/user/marketing && python cli.py $ARGUMENTS
```

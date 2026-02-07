# Stock Selector
## EPS Estimation & Dividend Yield–Based Stock Screening System

---

## Project Overview

This project implements a **fundamental-analysis–based stock screening system** focusing on:

- Estimating future Earnings Per Share (EPS)
- Estimating expected cash dividends
- Calculating dividend yield based on current stock prices
- Screening stocks with stable and relatively high dividend yields

The system follows a **long-term investment philosophy** and is designed for
academic research and educational purposes rather than short-term trading.

Financial data is retrieved using **Yahoo Finance via the `yfinance` library**.

---

## Motivation

For long-term investors, the most important questions are:

1. Can the company generate stable profits?
2. Does the company consistently share profits with shareholders?
3. Is the current stock price attractive given the expected dividend yield?

This project aims to answer these questions in a systematic and reproducible way.

---

## Core Logic

The stock screening process consists of the following steps:

1. EPS Estimation  
   - Use historical EPS data (e.g., past 3–5 years)  
   - Estimate the current-year EPS using a simple statistical method
     (average or trend-based)

2. Dividend Estimation  
   - Compute the historical average payout ratio  
   - Estimate expected cash dividends:

   Expected Dividend = Estimated EPS × Average Payout Ratio

3. Dividend Yield Calculation  

   Dividend Yield = Expected Dividend / Current Stock Price

4. Stock Screening  
   - Remove stocks with missing or insufficient data  
   - Rank stocks by estimated dividend yield  
   - Select stocks above a predefined threshold (e.g., 6% or 7%)

---

## Current Features

- Data Collection  
  - EPS  
  - Dividends  
  - Stock price  
  - Shares outstanding (when available)  
  - Source: Yahoo Finance (`yfinance`)

- Rule-Based EPS Estimation  
  - Simple and interpretable  
  - Easy to extend to machine-learning models

- Dividend Yield Estimation  
  - Based on estimated EPS and historical payout ratios

- Stock Ranking and Filtering  
  - Yield-based screening  
  - Clean output for further analysis

---

## Tech Stack

- Language: Python  
- Data Source: Yahoo Finance  
- Libraries:
  - yfinance  
  - pandas  
  - numpy  

---

## Usage

Install required packages:

pip install yfinance pandas numpy

Run the program:

python stock_selector.py

You can modify the stock list and screening thresholds directly in the script.

---

## Project Scope

- No short-term trading strategies  
- No technical indicators (e.g., MACD, RSI, candlestick patterns)  
- No stock price prediction  

- Fundamental analysis only  
- Long-term investment oriented  
- Designed for academic and research use  

---

## Limitations

- Yahoo Finance data may be incomplete for some stocks  
- EPS estimation is currently rule-based  
- No backtesting module yet  
- Dividend policy changes are not dynamically modeled  

---

## Future Work

- Machine-learning–based EPS forecasting  
- Multi-scenario EPS estimation (conservative / neutral / optimistic)  
- Integration with revenue and margin models  
- Backtesting and performance evaluation  
- Automated stock universe updates  

---

## Author

Yuan 
Background: Computer Science / Information Engineering  

This project is developed for academic research and educational purposes.  
Collaboration and extensions are welcome.

## Acknowledgment

I would like to thank a peer who provided assistance in refactoring
and integrating existing code modules during the development of
this project.


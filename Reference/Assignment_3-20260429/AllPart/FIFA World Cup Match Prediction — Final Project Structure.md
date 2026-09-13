# FIFA World Cup Match Prediction — Final Project Structure

PHASE 1 — PROJECT SETUP AND DATA LOADING
│
├── 1.1 Project Overview
├── 1.2 Import Libraries
├── 1.3 Reproducibility Configuration
├── 1.4 Upload Dataset
├── 1.5 Load results.csv
└── 1.6 Preserve Raw Dataset

PHASE 2 — INITIAL DATA AUDIT
│
├── 2.1 Preview Raw Dataset
├── 2.2 Dataset Dimensions
├── 2.3 Dataset Information and Data Types
├── 2.4 Missing Value Audit
├── 2.5 Duplicate Record Audit
├── 2.6 Date Range Audit
├── 2.7 Unique Value Summary
├── 2.8 Tournament Distribution
├── 2.9 FIFA World Cup Record Analysis
└── 2.10 Investigate Missing Score Records

PHASE 3 — DATA CLEANING
│
├── 3.1 Convert Date Data Type
├── 3.2 Sort Matches Chronologically
├── 3.3 Separate Completed Matches and Prediction Fixtures
└── 3.4 Verify Duplicate Records

PHASE 4 — TARGET VARIABLE CONSTRUCTION
│
├── 4.1 Create Match Outcome Target
├── 4.2 Validate Target Labels
├── 4.3 Analyse Overall Target Distribution
├── 4.4 Analyse World Cup Target Distribution
└── 4.5 Data Leakage Control

PHASE 5 — HISTORICAL FEATURE ENGINEERING
│
├── 5.1 Build Complete Chronological Timeline
├── 5.2 Define Team Performance Feature Function
├── 5.3 Define Leakage-Free Historical Feature Generator
├── 5.4 Generate Historical Features
├── 5.5 Preview Engineered Features
├── 5.6 Validate Temporal Leakage Prevention
├── 5.7 Inspect a Modern World Cup Match Example
├── 5.8 Separate Model Data and Prediction Data
└── 5.9 Audit Cold-Start Missing Values

PHASE 6 — FINAL MODELLING DATASET PREPARATION
│
├── 6.1 Calculate Cold-Start Fallback Values
├── 6.2 Apply Cold-Start Treatment
├── 6.3 Create Team Strength Difference Features
├── 6.4 Create Tournament Categories
├── 6.5 One-Hot Encode Tournament Categories
├── 6.6 Encode Neutral Venue
├── 6.7 Define Final Predictor Variables
└── 6.8 Build X and y

PHASE 7 — CHRONOLOGICAL TRAIN-TEST SPLIT
│
├── 7.1 Perform 80/20 Chronological Split
├── 7.2 Validate Temporal Separation
├── 7.3 Compare Training and Testing Class Distribution
└── 7.4 Create FIFA World Cup Test Subset

PHASE 8 — LOGISTIC REGRESSION
│
├── 8.1 Standardise Numerical Features
├── 8.2 Train Logistic Regression
├── 8.3 Generate Predictions
├── 8.4 Evaluate Overall Test Performance
└── 8.5 Evaluate World Cup Performance

PHASE 9 — DECISION TREE
│
├── 9.1 Configure Decision Tree
├── 9.2 Train Decision Tree
├── 9.3 Generate Predictions
├── 9.4 Evaluate Overall Test Performance
├── 9.5 Evaluate World Cup Performance
└── 9.6 Visualise Decision Tree

PHASE 10 — RANDOM FOREST
│
├── 10.1 Configure Random Forest
├── 10.2 Train Random Forest
├── 10.3 Generate Predictions
├── 10.4 Evaluate Overall Test Performance
├── 10.5 Evaluate World Cup Performance
└── 10.6 Extract Feature Importance

PHASE 11 — MODEL EVALUATION AND COMPARISON
│
├── 11.1 Create Shared Evaluation Function
├── 11.2 Compare Accuracy
├── 11.3 Compare Macro Precision
├── 11.4 Compare Macro Recall
├── 11.5 Compare Macro F1-Score
├── 11.6 Compare Confusion Matrices
├── 11.7 Compare World Cup-Specific Performance
└── 11.8 Identify Best Model

PHASE 12 — DATA VISUALISATION AND RESULT ANALYSIS
│
├── 12.1 Match Outcome Distribution
├── 12.2 Tournament Distribution
├── 12.3 Match Volume Over Time
├── 12.4 Overall Model Performance Comparison
├── 12.5 World Cup Model Performance Comparison
├── 12.6 Confusion Matrix Visualisations
├── 12.7 Random Forest Feature Importance
└── 12.8 Actual vs Predicted Outcome Distribution

PHASE 13 — FINAL FIFA WORLD CUP PREDICTION
│
├── 13.1 Prepare Unscored World Cup Fixtures
├── 13.2 Apply Best Trained Model
├── 13.3 Generate Predicted Outcomes
├── 13.4 Generate Prediction Probabilities
└── 13.5 Present Final Prediction Table

PHASE 14 — PROJECT SUMMARY AND REPRODUCIBILITY
│
├── 14.1 Summarise Dataset Transformation
├── 14.2 Summarise Final Features
├── 14.3 Summarise Model Results
├── 14.4 State Best Performing Model
└── 14.5 Reproducibility Information
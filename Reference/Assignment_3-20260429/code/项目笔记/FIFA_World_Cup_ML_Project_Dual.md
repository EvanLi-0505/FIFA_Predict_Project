# 基于机器学习的 FIFA 世界杯比赛结果预测
# Machine Learning-Based Prediction of FIFA World Cup Match Results

## 项目文档 / Project Documentation

> 本文档详细说明项目目的、功能、项目结构、完整数据流程，以及 Notebook 中每个 Phase 和 Cell 的作用。
>
> This document explains the project purpose, functionality, structure, complete data pipeline, and the role of every Phase and Cell in the notebook.

---

# 1. 项目概述 / Project Overview

## 1.1 项目名称 / Project Title

**Machine Learning-Based Prediction of FIFA World Cup Match Results**

## 1.2 项目目的 / Project Purpose

本项目开发了一套完整的机器学习流程，用于预测国际足球比赛结果，并重点关注 FIFA 世界杯比赛。

This project develops a complete machine learning pipeline for predicting international football match outcomes, with a particular focus on FIFA World Cup matches.

The system uses historical international football match data to:

- clean and validate raw match records;
- explore important patterns in the dataset;
- transform raw match information into machine-learning-ready features;
- prevent temporal data leakage;
- train and compare multiple classification models;
- evaluate models on both a general test set and a FIFA World Cup-specific test subset;
- select a final model using suitable multi-class evaluation criteria;
- visualise model performance and prediction behaviour;
- retrain the selected model using all completed historical matches;
- predict future unscored FIFA World Cup matches;
- produce class probabilities and confidence levels;
- summarise the complete workflow and verify reproducibility.

The prediction target contains three classes:

1. **Home Win**
2. **Draw**
3. **Home Loss**

The project compares three machine learning algorithms:

- Logistic Regression
- Decision Tree
- Random Forest

最终选择的模型为 **Decision Tree（决策树）**，主要原因是它取得了最高的 FIFA World Cup Macro F1-Score，并且对平局具有较有意义的识别能力。

The final selected model is the **Decision Tree**, primarily because it achieved the highest FIFA World Cup Macro F1-Score and demonstrated meaningful recognition of drawn matches.

---

# 2. 项目主要功能 / Main Project Functions

The project provides the following major functions.

## 2.1 历史比赛数据处理 / Historical Match Data Processing

The notebook imports historical international football match data and performs:

- date conversion;
- duplicate inspection;
- missing-value analysis;
- invalid-value checks;
- target-variable creation;
- tournament categorisation.

## 2.2 探索性数据分析 / Exploratory Data Analysis

The project investigates:

- match outcome distribution;
- tournament distribution;
- neutral venue distribution;
- historical trends;
- FIFA World Cup-specific data availability.

This helps explain the characteristics and limitations of the dataset before modelling.

## 2.3 历史特征工程 / Historical Feature Engineering

Raw match records alone do not directly describe team strength. Therefore, the project creates historical performance features based only on matches played before each target match.

Examples include:

- recent win rate;
- recent draw rate;
- average goals scored;
- average goals conceded;
- recent goal difference;
- historical matches available.

A rolling historical window of the previous **5 matches** is used.

## 2.4 对比特征构建 / Comparative Feature Construction

The project creates difference-based features that compare the two teams directly.

Examples include:

- win rate difference;
- draw rate difference;
- goals scored difference;
- goals conceded difference;
- goal difference difference;
- experience difference.

These features help the model understand the relative strength of the home and away teams.

## 2.5 锦标赛与比赛情境编码 / Tournament and Match Context Encoding

The model also receives contextual information:

- whether the match is played at a neutral venue;
- whether the tournament is a Friendly;
- Other Competitive match;
- FIFA World Cup;
- FIFA World Cup Qualification match.

## 2.6 时间数据泄漏防止 / Temporal Leakage Prevention

The project uses a strict chronological workflow.

Historical features for each match are calculated only from matches that occurred earlier. The train-test split is also chronological rather than random.

This prevents future information from leaking into past training examples.

## 2.7 模型训练与评估 / Model Training and Evaluation

Three models are trained and evaluated:

- Logistic Regression;
- Decision Tree;
- Random Forest.

Each model is evaluated on:

1. the overall chronological test set;
2. the FIFA World Cup test subset.

The following metrics are used:

- Accuracy;
- Macro Precision;
- Macro Recall;
- Macro F1-Score;
- class-level Precision, Recall and F1-Score.

## 2.8 未来 FIFA 世界杯比赛预测 / Future FIFA World Cup Prediction

After selecting the final model, the project:

- identifies future unscored World Cup matches;
- validates their features;
- retrains the selected model using all completed matches;
- predicts the future outcomes;
- generates class probabilities;
- assigns prediction confidence levels.

---

# 3. 项目结构 / Project Structure

Notebook 共分为 **14 个主要阶段（Phases）**，从原始数据加载一直到未来比赛预测和可复现性验证。

The notebook is organised into fourteen major phases.

```text
Machine Learning-Based Prediction of FIFA World Cup Match Results
│
├── PHASE 1 — 项目设置与数据加载 / PROJECT SETUP AND DATA LOADING
│   ├── Import libraries
│   ├── Configure notebook environment
│   ├── Load dataset
│   └── Perform initial dataset inspection
│
├── PHASE 2 — 数据质量评估 / DATA QUALITY ASSESSMENT
│   ├── Inspect dataset structure
│   ├── Check data types
│   ├── Analyse missing values
│   ├── Check duplicate records
│   └── Validate important columns
│
├── PHASE 3 — 数据清洗与准备 / DATA CLEANING AND PREPARATION
│   ├── Convert dates
│   ├── Clean invalid records
│   ├── Create match result target
│   └── Prepare cleaned dataset
│
├── PHASE 4 — 探索性数据分析 / EXPLORATORY DATA ANALYSIS
│   ├── Analyse outcome distribution
│   ├── Analyse tournament distribution
│   ├── Analyse neutral venues
│   └── Explore historical patterns
│
├── PHASE 5 — 锦标赛分类 / TOURNAMENT CATEGORISATION
│   ├── Group tournament names
│   ├── Create tournament categories
│   └── Validate category distribution
│
├── PHASE 6 — 历史特征工程 / HISTORICAL FEATURE ENGINEERING
│   ├── Create rolling historical team features
│   ├── Prevent temporal leakage
│   ├── Create comparative features
│   ├── Handle cold-start records
│   └── Validate engineered features
│
├── PHASE 7 — 建模数据集准备 / MODELLING DATASET PREPARATION
│   ├── Build final modelling dataset
│   ├── Select predictor variables
│   ├── Encode tournament categories
│   ├── Create chronological train-test split
│   ├── Validate temporal separation
│   └── Create FIFA World Cup test subset
│
├── PHASE 8 — 逻辑回归 / LOGISTIC REGRESSION
│   ├── Train model
│   ├── Evaluate overall test performance
│   ├── Evaluate World Cup performance
│   └── Store results
│
├── PHASE 9 — 决策树 / DECISION TREE
│   ├── Train model
│   ├── Evaluate overall test performance
│   ├── Evaluate World Cup performance
│   └── Store results
│
├── PHASE 10 — 随机森林 / RANDOM FOREST
│   ├── Train model
│   ├── Evaluate overall test performance
│   ├── Evaluate World Cup performance
│   ├── Analyse feature importance
│   └── Store results
│
├── PHASE 11 — 模型比较与选择 / MODEL COMPARISON AND SELECTION
│   ├── Compare overall performance
│   ├── Compare World Cup performance
│   ├── Compare draw recognition
│   ├── Identify metric leaders
│   └── Select final model
│
├── PHASE 12 — 数据可视化 / DATA VISUALISATION
│   ├── Overall model comparison chart
│   ├── World Cup model comparison chart
│   ├── Confusion matrix
│   ├── Draw recognition chart
│   ├── Feature importance chart
│   └── Actual vs predicted distribution chart
│
├── PHASE 13 — 未来 FIFA 世界杯预测 / FUTURE FIFA WORLD CUP PREDICTION
│   ├── Identify future unscored matches
│   ├── Validate prediction features
│   ├── Build final retraining dataset
│   ├── Retrain selected model
│   ├── Predict future matches
│   ├── Generate probabilities
│   └── Visualise future predictions
│
└── PHASE 14 — 项目总结与可复现性 / PROJECT SUMMARY AND REPRODUCIBILITY
    ├── Summarise dataset transformation
    ├── Summarise final features
    ├── Summarise model results
    ├── State final model selection
    └── Verify reproducibility
```

---

# 4. 整体数据流程 / Overall Data Flow

完整项目流程如下。该流程展示数据如何从原始比赛记录逐步转换为最终预测结果。

The complete project pipeline is:

```text
Raw International Football Match Dataset
                │
                ▼
Data Loading and Initial Inspection
                │
                ▼
Data Quality Assessment
                │
                ▼
Data Cleaning and Target Creation
                │
                ▼
Exploratory Data Analysis
                │
                ▼
Tournament Categorisation
                │
                ▼
Historical Feature Engineering
(previous 5 matches only)
                │
                ▼
Cold-Start Treatment and Feature Validation
                │
                ▼
Final 23 Predictor Variables
                │
                ▼
Completed Matches / Future Unscored Matches
        │                       │
        ▼                       ▼
Modelling Dataset        Future Prediction Dataset
        │
        ▼
Chronological 80/20 Split
        │
        ├───────────────┐
        ▼               ▼
Training Set        Overall Test Set
                        │
                        ▼
                World Cup Test Subset
        │
        ▼
Train Three Models
        │
        ├── Logistic Regression
        ├── Decision Tree
        └── Random Forest
        │
        ▼
Overall and World Cup Evaluation
        │
        ▼
Model Comparison
        │
        ▼
Select Decision Tree
        │
        ▼
Retrain on All 49,495 Completed Matches
        │
        ▼
Predict 7 Future FIFA World Cup Matches
        │
        ▼
Prediction Probabilities and Confidence Levels
        │
        ▼
Project Summary and Reproducibility Validation
```

---

# 5. 各 Phase 与 Cell 说明 / Phase-by-Phase and Cell-by-Cell Explanation

# PHASE 1 — 项目设置与数据加载 / PROJECT SETUP AND DATA LOADING

## 作用 / Purpose

Phase 1 用于建立 Notebook 运行环境并加载原始足球比赛数据。

Phase 1 establishes the notebook environment and loads the raw football dataset.

### Cell 1.1 — 导入所需库 / Import Required Libraries

Imports the Python libraries required for:

- data manipulation;
- numerical processing;
- visualisation;
- machine learning;
- model evaluation.

### Cell 1.2 — 配置 Notebook 环境 / Configure Notebook Environment

Sets notebook-wide display and analysis options so tables and outputs are easier to inspect consistently.

### Cell 1.3 — 加载数据集 / Load the Dataset

Reads the international football results dataset into a Pandas DataFrame.

### Cell 1.4 — 初步检查数据集 / Initial Dataset Inspection

Displays basic information such as:

- dataset shape;
- first rows;
- column names;
- basic data types.

Its purpose is to understand the raw dataset before modifying it.

---

# PHASE 2 — 数据质量评估 / DATA QUALITY ASSESSMENT

## 作用 / Purpose

Phase 2 用于检查原始数据是否适合分析，并识别需要处理的数据质量问题。

Phase 2 checks whether the raw data is suitable for analysis and identifies quality problems that must be addressed.

### Cell 2.1 — 检查数据集维度与列 / Inspect Dataset Dimensions and Columns

Reports the number of records and variables and verifies the expected schema.

### Cell 2.2 — 检查数据类型 / Inspect Data Types

Checks whether dates, scores, text fields and Boolean fields use suitable data types.

### Cell 2.3 — 缺失值分析 / Missing Value Analysis

Counts missing values and calculates missing percentages for each column.

### Cell 2.4 — 重复记录分析 / Duplicate Record Analysis

Checks whether exact or potentially duplicated match records exist.

### Cell 2.5 — 比分与比赛记录验证 / Score and Match Record Validation

Checks important fields for invalid or inconsistent values before feature engineering.

---

# PHASE 3 — 数据清洗与准备 / DATA CLEANING AND PREPARATION

## 作用 / Purpose

Phase 3 将原始数据集转换为可靠、可用于后续分析的数据集。

Phase 3 converts the raw dataset into a reliable analytical dataset.

### Cell 3.1 — 转换比赛日期 / Convert Match Date

Converts the date column into a proper datetime format and prepares the dataset for chronological processing.

### Cell 3.2 — 按时间顺序排列比赛 / Sort Matches Chronologically

Orders all matches from earliest to latest.

This is essential because later historical features depend on earlier matches.

### Cell 3.3 — 清理无效或不完整记录 / Clean Invalid or Incomplete Records

Handles records that cannot be safely used in the modelling workflow.

### Cell 3.4 — 创建比赛结果目标变量 / Create Match Outcome Target

Creates the target variable from home and away scores:

- Home Win;
- Draw;
- Home Loss.

### Cell 3.5 — 验证清洗后的数据集 / Validate Cleaned Dataset

Confirms that the cleaned dataset and target variable are correctly constructed.

---

# PHASE 4 — 探索性数据分析 / EXPLORATORY DATA ANALYSIS

## 作用 / Purpose

Phase 4 在建模前探索足球数据集的主要特征与分布规律。

Phase 4 explores the characteristics of the football dataset before modelling.

### Cell 4.1 — 比赛结果分布 / Match Outcome Distribution

Examines the number and proportion of:

- Home Wins;
- Draws;
- Home Losses.

This reveals class imbalance.

### Cell 4.2 — 锦标赛分布 / Tournament Distribution

Examines which tournaments contribute the largest number of matches.

### Cell 4.3 — 中立场地分析 / Neutral Venue Analysis

Investigates the distribution of neutral and non-neutral matches.

### Cell 4.4 — 历史比赛趋势分析 / Historical Match Trend Analysis

Examines how the number of recorded international matches changes over time.

### Cell 4.5 — FIFA 世界杯数据探索 / FIFA World Cup Data Exploration

Inspects the availability and characteristics of World Cup matches in the dataset.

---

# PHASE 5 — 锦标赛分类 / TOURNAMENT CATEGORISATION

## 作用 / Purpose

The original dataset contains many tournament names. Phase 5 reduces this complexity by grouping tournaments into meaningful categories.

### Cell 5.1 — 检查唯一锦标赛名称 / Inspect Unique Tournament Names

Reviews the tournament values present in the dataset.

### Cell 5.2 — 定义锦标赛分类逻辑 / Define Tournament Categorisation Logic

Creates rules that map tournament names into broader groups.

### Cell 5.3 — 创建锦标赛类别特征 / Create Tournament Category Feature

Assigns each match to one of four categories:

- Friendly;
- Other Competitive;
- World Cup;
- World Cup Qualification.

### Cell 5.4 — 锦标赛类别分布 / Tournament Category Distribution

Counts the number of matches in each category and validates the categorisation.

The final distribution contains:

- Other Competitive: 21,282;
- Friendly: 18,388;
- World Cup Qualification: 8,771;
- World Cup: 1,054.

---

# PHASE 6 — 历史特征工程 / HISTORICAL FEATURE ENGINEERING

## 作用 / Purpose

Phase 6 是整个项目的核心特征工程阶段。

Phase 6 is the core feature engineering stage.

It converts historical match results into measures of recent team performance while preventing temporal leakage.

The historical window uses the previous **5 matches**.

### Cell 6.1 — 初始化历史特征工程 / Initialise Historical Feature Engineering

Prepares the chronological dataset and structures required to calculate team histories.

### Cell 6.2 — 计算主队历史特征 / Calculate Home Team Historical Features

Calculates the home team's performance using only matches played before the current match.

### Cell 6.3 — 计算客队历史特征 / Calculate Away Team Historical Features

Calculates equivalent historical performance features for the away team.

### Cell 6.4 — 创建近期表现特征 / Create Recent Performance Features

Creates:

- `home_recent_win_rate`;
- `away_recent_win_rate`;
- `home_recent_draw_rate`;
- `away_recent_draw_rate`.

### Cell 6.5 — 创建进球表现特征 / Create Goal Performance Features

Creates:

- average goals scored;
- average goals conceded;
- recent goal difference;

for both home and away teams.

### Cell 6.6 — 创建历史经验特征 / Create Historical Experience Features

Creates:

- `home_matches_available`;
- `away_matches_available`.

These indicate how many historical matches were available when the feature was calculated.

### Cell 6.7 — 时间数据泄漏验证 / Temporal Leakage Validation

Uses the earliest match in the dataset to verify that no future match information is used.

For the first historical match, both teams correctly have zero previous matches.

### Cell 6.8 — 创建对比差异特征 / Create Comparative Difference Features

Creates direct comparisons between the home and away teams:

- `win_rate_difference`;
- `draw_rate_difference`;
- `goals_scored_difference`;
- `goals_conceded_difference`;
- `goal_difference_difference`;
- `experience_difference`.

### Cell 6.9 — 检查工程特征缺失值 / Inspect Engineered Feature Missing Values

Checks missing values created by teams with insufficient historical data.

The missing values are expected cold-start effects rather than data corruption.

### Cell 6.10 — 应用冷启动处理 / Apply Cold-Start Treatment

Replaces unavailable historical statistics using the chosen cold-start strategy.

The output confirms:

- missing engineered values before treatment: 1,680;
- missing engineered values after treatment: 0.

### Cell 6.11 — 验证特征工程数据集 / Validate Engineered Feature Dataset

Checks the completed feature-engineered dataset for:

- missing values;
- invalid values;
- feature consistency.

### Cell 6.12 — 检查工程特征样本 / Inspect Engineered Feature Sample

Displays example records to verify that the historical features are sensible.

### Cell 6.13 — 完成历史特征工程 / Complete Historical Feature Engineering

Reports the final Phase 6 output:

- 49,502 processed records;
- rolling window of 5 matches;
- 22 columns after historical feature engineering.

---

# PHASE 7 — 建模数据集准备 / MODELLING DATASET PREPARATION

## 作用 / Purpose

Phase 7 将特征工程后的数据转换为最终监督学习数据集。

Phase 7 transforms the engineered dataset into the final supervised learning dataset.

### Cell 7.1 — 准备已完成比赛记录 / Prepare Completed Match Records

Separates matches with known outcomes from future unscored matches.

The modelling dataset contains 49,495 completed matches.

### Cell 7.2 — 编码锦标赛类别 / Encode Tournament Categories

Converts tournament categories into machine-learning-compatible dummy variables.

### Cell 7.3 — 定义最终预测特征 / Define Final Predictor Features

Defines the final list of 23 predictor variables.

### Cell 7.4 — 创建 FIFA 世界杯测试子集 / Create FIFA World Cup Test Subset

Creates a dedicated World Cup subset from the chronological test data.

The final subset contains 218 matches from 2018-06-14 to 2026-07-04.

### Cell 7.5 — 构建最终建模数据集 / Build Final Modelling Dataset

Creates:

- predictor matrix `X`;
- target vector `y`.

The final shapes are:

- `X`: 49,495 rows × 23 predictors;
- `y`: 49,495 outcomes.

### Cell 7.6 — 验证最终建模数据集 / Validate Final Modelling Dataset

Checks that the predictor matrix contains:

- zero missing values;
- zero infinite values;
- all three target classes.

### Cell 7.7 — 创建按时间顺序的训练测试划分 / Create Chronological Train-Test Split

Splits the data chronologically:

- 80% training;
- 20% testing.

Final sizes:

- training: 39,587 records;
- testing: 9,908 records.

### Cell 7.8 — 验证严格时间分离 / Validate Strict Temporal Separation

Confirms:

- latest training date: 2016-03-28;
- earliest testing date: 2016-03-29.

This proves that training and testing periods do not overlap.

### Cell 7.9 — 比较训练集与测试集类别分布 / Compare Training and Testing Class Distribution

Checks whether outcome proportions remain reasonably similar across the chronological split.

### Cell 7.10 — 验证 FIFA 世界杯测试数据 / Validate FIFA World Cup Test Data

Confirms that the dedicated World Cup subset is ready for model-specific evaluation.

---

# PHASE 8 — 逻辑回归 / LOGISTIC REGRESSION

## 作用 / Purpose

Phase 8 训练第一个基线分类模型：逻辑回归。

Phase 8 trains the first baseline classification model.

### Cell 8.1 — 配置逻辑回归 / Configure Logistic Regression

Creates the Logistic Regression model with the required settings.

### Cell 8.2 — 训练逻辑回归 / Train Logistic Regression

Fits the model using the chronological training set.

### Cell 8.3 — 预测整体测试集 / Predict Overall Test Set

Generates predictions for the complete chronological test set.

### Cell 8.4 — 评估整体测试表现 / Evaluate Overall Test Performance

Calculates:

- Accuracy;
- Macro Precision;
- Macro Recall;
- Macro F1-Score;
- classification report.

### Cell 8.5 — 评估 FIFA 世界杯表现 / Evaluate FIFA World Cup Performance

Tests the same model specifically on the 218-match World Cup subset.

### Cell 8.6 — 保存逻辑回归结果 / Store Logistic Regression Results

Stores overall and World Cup metrics for later comparison.

---

# PHASE 9 — 决策树 / DECISION TREE

## 作用 / Purpose

Phase 9 训练并评估 Decision Tree（决策树）模型。

Phase 9 trains and evaluates the Decision Tree model.

### Cell 9.1 — 配置决策树 / Configure Decision Tree

Creates the Decision Tree classifier using controlled hyperparameters.

The final documented settings include:

- maximum depth: 10;
- minimum samples split: 20;
- minimum samples leaf: 10;
- random state: 42.

### Cell 9.2 — 训练决策树 / Train Decision Tree

Fits the model on the chronological training data.

### Cell 9.3 — 预测整体测试集 / Predict Overall Test Set

Generates Decision Tree predictions for the full test set.

### Cell 9.4 — 评估整体测试表现 / Evaluate Overall Test Performance

Calculates overall metrics and the class-level classification report.

### Cell 9.5 — 评估 FIFA 世界杯表现 / Evaluate FIFA World Cup Performance

Evaluates the Decision Tree on the dedicated World Cup subset.

### Cell 9.6 — 保存决策树结果 / Store Decision Tree Results

Stores all metrics for later model comparison.

---

# PHASE 10 — 随机森林 / RANDOM FOREST

## 作用 / Purpose

Phase 10 训练 Random Forest（随机森林）集成模型，并分析特征重要性。

Phase 10 trains the Random Forest ensemble model and analyses feature importance.

### Cell 10.1 — 配置随机森林 / Configure Random Forest

Creates the Random Forest classifier with reproducible settings.

### Cell 10.2 — 训练随机森林 / Train Random Forest

Fits the ensemble model using the training data.

### Cell 10.3 — 预测整体测试集 / Predict Overall Test Set

Generates predictions for the complete test set.

### Cell 10.4 — 评估整体测试表现 / Evaluate Overall Test Performance

Calculates all overall evaluation metrics.

### Cell 10.5 — 评估 FIFA 世界杯表现 / Evaluate FIFA World Cup Performance

Measures model performance specifically on World Cup matches.

### Cell 10.6 — 分析随机森林特征重要性 / Analyse Random Forest Feature Importance

Ranks all 23 predictors according to their contribution to Random Forest predictions.

The most important features include:

- `goal_difference_difference`;
- `goals_conceded_difference`;
- recent goal difference features;
- `goals_scored_difference`.

### Cell 10.7 — 保存随机森林结果 / Store Random Forest Results

Stores the model metrics for Phase 11 comparison.

---

# PHASE 11 — 模型比较与选择 / MODEL COMPARISON AND SELECTION

## 作用 / Purpose

Phase 11 比较全部模型，并决定哪个模型用于未来世界杯比赛预测。

Phase 11 compares all models and determines which model should be used for future World Cup prediction.

### Cell 11.1 — 整体测试集模型比较 / Overall Test Model Comparison

Compares the three models using:

- Accuracy;
- Macro Precision;
- Macro Recall;
- Macro F1-Score.

### Cell 11.2 — FIFA 世界杯模型比较 / FIFA World Cup Model Comparison

Repeats the comparison using only the World Cup test subset.

### Cell 11.3 — 平局识别能力比较 / Draw Recognition Comparison

Compares Draw:

- Precision;
- Recall;
- F1-Score.

This is important because draws are the hardest class to predict.

### Cell 11.4 — 按指标识别最佳模型 / Identify Best Model by Metric

Determines the best-performing model for each evaluation metric.

### Cell 11.5 — 创建最终评估总结 / Create Final Evaluation Summary

Summarises the key leaders:

- highest overall accuracy: Random Forest;
- highest overall Macro F1: Decision Tree;
- highest World Cup accuracy: Logistic Regression;
- highest World Cup Macro F1: Decision Tree;
- best World Cup draw recognition: Decision Tree.

### Cell 11.6 — 选择最终模型 / Select Final Model

Selects **Decision Tree** as the final model.

The primary selection criterion is the highest FIFA World Cup Macro F1-Score.

---

# PHASE 12 — 数据可视化 / DATA VISUALISATION

## 作用 / Purpose

Phase 12 将评估结果转换为便于解释和用于最终报告的图表。

Phase 12 converts the evaluation results into charts suitable for interpretation and the final report.

### Cell 12.1 — 整体测试表现比较 / Overall Test Performance Comparison

Creates a grouped bar chart comparing the three models on:

- Accuracy;
- Macro Precision;
- Macro Recall;
- Macro F1-Score.

### Cell 12.2 — FIFA 世界杯预测表现 / FIFA World Cup Prediction Performance

Creates the equivalent comparison chart for the World Cup subset.

### Cell 12.3 — FIFA 世界杯混淆矩阵 / FIFA World Cup Confusion Matrix

Visualises actual and predicted classes for the selected model.

The confusion matrix shows where the model correctly predicts outcomes and where it confuses classes.

### Cell 12.4 — FIFA 世界杯平局识别表现 / FIFA World Cup Draw Recognition Performance

Compares Draw Recall and Draw F1-Score across all three models.

This chart clearly demonstrates the Decision Tree's advantage in draw recognition.

### Cell 12.5 — 前 10 个最重要预测特征 / Top 10 Most Important Predictive Features

Visualises the ten most influential Random Forest predictors.

This provides model interpretability and identifies the strongest football performance indicators.

### Cell 12.6 — 世界杯实际与预测结果分布 / Actual vs Predicted World Cup Outcome Distribution

Compares:

- actual outcome counts;
- Logistic Regression predictions;
- Decision Tree predictions;
- Random Forest predictions.

This exposes prediction bias, particularly overprediction of Home Wins and underprediction of Draws.

---

# PHASE 13 — 未来 FIFA 世界杯预测 / FUTURE FIFA WORLD CUP PREDICTION

## 作用 / Purpose

Phase 13 将完整机器学习流程应用于未来尚未产生比赛结果的 FIFA 世界杯比赛。

Phase 13 applies the completed machine learning workflow to future unscored FIFA World Cup matches.

### Cell 13.1 — 识别未来未出结果的 FIFA 世界杯比赛 / Identify Future Unscored FIFA World Cup Matches

Separates future World Cup fixtures that do not yet have final scores.

The final dataset contains 7 future matches from 2026-07-05 to 2026-07-09.

### Cell 13.2 — 验证未来比赛预测特征 / Validate Future Match Prediction Features

Checks whether all 23 required predictor columns are present.

It also checks:

- missing values;
- infinite values.

The final validation confirms that all future matches contain complete predictor values.

### Cell 13.3 — 构建最终模型重训练数据集 / Build Final Model Retraining Dataset

Creates the final training dataset from all 49,495 completed matches.

This allows the final model to learn from all known historical outcomes before future prediction.

### Cell 13.4 — 重新训练选定的决策树 / Retrain the Selected Decision Tree

Fits a new Decision Tree using all completed matches and the same documented model settings.

### Cell 13.5 — 生成未来比赛预测 / Generate Future Match Predictions

Predicts the outcome of each future FIFA World Cup match.

### Cell 13.6 — 创建最终预测结果 / Create Final Prediction Results

Produces a clean results table containing:

- date;
- home team;
- away team;
- predicted result;
- prediction confidence.

### Cell 13.7 — 生成详细预测概率 / Generate Detailed Prediction Probabilities

Calculates probabilities for all three possible outcomes:

- Home Win;
- Draw;
- Home Loss.

It also identifies the highest probability as the predicted result.

### Cell 13.8 — 分配预测置信度等级 / Assign Prediction Confidence Levels

Converts the maximum predicted probability into an interpretable confidence category such as:

- Very Low;
- Low;
- Moderate;
- High;
- Very High.

### Cell 13.9 — 可视化未来比赛预测概率 / Visualise Future Match Prediction Probabilities

Creates a grouped bar chart showing the three outcome probabilities for each future World Cup match.

This makes uncertainty visible rather than showing only the final predicted class.

---

# PHASE 14 — 项目总结与可复现性 / PROJECT SUMMARY AND REPRODUCIBILITY

## 作用 / Purpose

Phase 14 对完整项目进行最终总结与审查。

Phase 14 provides a final audit of the complete project.

It verifies that the data flow, features, model results and reproducibility information are internally consistent.

### Cell 14.1 — 总结数据集转换过程 / Summarise Dataset Transformation

Creates a complete record-count summary from:

- original dataset;
- feature-engineered dataset;
- completed modelling matches;
- final predictor matrix;
- training set;
- testing set;
- World Cup test subset;
- future prediction set.

It also validates:

```text
49,495 completed matches
+ 7 future matches
= 49,502 feature-engineered records
```

### Cell 14.2 — 总结最终特征 / Summarise Final Features

Documents all 23 predictor variables and their categories.

Feature groups are:

- Recent Performance: 10;
- Historical Experience: 2;
- Comparative Difference: 6;
- Match Context: 1;
- Tournament Category: 4.

The cell confirms that all documented features match the final model input.

### Cell 14.3 — 总结最终模型结果 / Summarise Final Model Results

Combines the evaluation results for all three models across:

- Overall Test Set;
- FIFA World Cup Test Subset.

It also identifies performance leaders by evaluation criterion.

### Cell 14.4 — 说明最佳模型 / State Best Performing Model

Documents the final model selection.

The selected model is:

**Decision Tree**

Primary criterion:

**Highest FIFA World Cup Macro F1-Score**

The cell also records the selected model's:

- overall accuracy;
- overall Macro F1;
- World Cup accuracy;
- World Cup Macro F1;
- World Cup Draw Recall;
- World Cup Draw F1-Score.

### Cell 14.5 — 可复现性信息 / Reproducibility Information

Documents the settings required to reproduce the experiment:

- random state: 42;
- chronological train-test split;
- training proportion: 80%;
- testing proportion: 20%;
- historical feature window: previous 5 matches;
- three target classes;
- 23 predictors;
- final Decision Tree model;
- Decision Tree hyperparameters;
- 7 future matches predicted;
- temporal leakage prevention strategy.

The cell also revalidates the chronological separation between training and testing data.

The pipeline ends with:

```text
PROJECT PIPELINE COMPLETED SUCCESSFULLY.
```

---

# 6. 最终预测特征 / Final Predictor Variables

最终模型共使用 **23 个预测变量（predictors）**。

The final model uses 23 predictors.

## 6.1 近期表现特征 / Recent Performance Features

1. `home_recent_win_rate`
2. `away_recent_win_rate`
3. `home_recent_draw_rate`
4. `away_recent_draw_rate`
5. `home_avg_goals_scored`
6. `away_avg_goals_scored`
7. `home_avg_goals_conceded`
8. `away_avg_goals_conceded`
9. `home_recent_goal_difference`
10. `away_recent_goal_difference`

## 6.2 历史经验特征 / Historical Experience Features

11. `home_matches_available`
12. `away_matches_available`

## 6.3 对比差异特征 / Comparative Difference Features

13. `win_rate_difference`
14. `draw_rate_difference`
15. `goals_scored_difference`
16. `goals_conceded_difference`
17. `goal_difference_difference`
18. `experience_difference`

## 6.4 比赛情境特征 / Match Context Feature

19. `neutral`

## 6.5 锦标赛类别特征 / Tournament Category Features

20. `tournament_Friendly`
21. `tournament_Other Competitive`
22. `tournament_World Cup`
23. `tournament_World Cup Qualification`

---

# 7. 关键数据集数量 / Key Dataset Numbers

| Dataset Stage | Number of Records |
|---|---:|
| Original Dataset | 49,502 |
| Feature-Engineered Dataset | 49,502 |
| Completed Matches | 49,495 |
| Final Predictor Matrix | 49,495 |
| Training Set | 39,587 |
| Testing Set | 9,908 |
| FIFA World Cup Test Subset | 218 |
| Future Unscored World Cup Matches | 7 |

The dataset accounting is complete:

```text
49,495 completed matches + 7 future matches = 49,502 total records
```

---

# 8. 最终模型表现总结 / Final Model Performance Summary

## 8.1 整体测试集 / Overall Test Set

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1-Score |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.5288 | 0.4809 | 0.4179 | 0.3650 |
| Decision Tree | 0.5165 | 0.4415 | 0.4183 | 0.3915 |
| Random Forest | 0.5303 | 0.4967 | 0.4200 | 0.3696 |

## 8.2 FIFA 世界杯测试子集 / FIFA World Cup Test Subset

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1-Score |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.5138 | 0.3481 | 0.4286 | 0.3753 |
| Decision Tree | 0.4725 | 0.4270 | 0.4053 | 0.3903 |
| Random Forest | 0.5000 | 0.3310 | 0.4130 | 0.3587 |

---

# 9. 为什么选择决策树 / Why Decision Tree Was Selected

选择 **Decision Tree（决策树）** 的主要原因如下：

The Decision Tree was selected because:

- it achieved the highest overall Macro F1-Score;
- it achieved the highest FIFA World Cup Macro F1-Score;
- it was the only model with meaningful World Cup draw recognition;
- Macro F1 is more appropriate than Accuracy alone for the three-class imbalanced prediction problem.

The project therefore prioritises balanced multi-class prediction rather than simply maximising the total number of correct predictions.

---

# 10. 重要方法论优势 / Important Methodological Strengths

## 10.1 严格按时间顺序评估 / Strict Chronological Evaluation

The project does not randomly shuffle historical football matches.

Training data ends on:

**2016-03-28**

Testing data begins on:

**2016-03-29**

This produces a realistic forecasting scenario.

## 10.2 防止时间数据泄漏 / Temporal Leakage Prevention

Every historical feature uses only information available before the match being predicted.

## 10.3 独立世界杯评估 / Dedicated World Cup Evaluation

The model is not selected only using general international football performance.

A dedicated 218-match World Cup subset is used because the final project objective focuses on FIFA World Cup prediction.

## 10.4 多指标评估 / Multi-Metric Evaluation

The project does not rely only on Accuracy.

It also evaluates:

- Precision;
- Recall;
- F1-Score;
- Macro averages;
- class-level performance;
- draw recognition.

## 10.5 未来预测不确定性 / Future Prediction Uncertainty

Future predictions include:

- probabilities for all three classes;
- prediction confidence percentage;
- confidence level.

This is more informative than returning only a single predicted result.

---

# 11. 项目局限性 / Project Limitations

本项目仍存在一些需要在报告中明确说明的局限性。

The project also has several limitations that should be acknowledged.

1. Historical football data does not include player-level information.
2. Injuries, suspensions and squad selections are not included.
3. FIFA rankings and Elo ratings are not included in the current 23 predictors.
4. Recent form uses a fixed five-match window.
5. Draws remain difficult to predict because they are less common and often depend on fine match-level factors.
6. Historical tournament conditions may differ from future tournaments.
7. Prediction probabilities represent model estimates rather than guaranteed real-world outcomes.

---

# 12. 最终项目状态 / Final Project Status

The completed project includes:

- data loading;
- quality assessment;
- cleaning;
- EDA;
- tournament categorisation;
- leakage-safe historical feature engineering;
- 23 final predictors;
- chronological train-test splitting;
- three machine learning models;
- general evaluation;
- World Cup-specific evaluation;
- model comparison;
- model selection;
- six major evaluation visualisations;
- future World Cup match prediction;
- detailed probability output;
- confidence-level interpretation;
- complete project summary;
- reproducibility validation.

**Final status: Project pipeline completed successfully.**

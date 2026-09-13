# FIFA World Cup Prediction System — Dual Web & Windows Desktop Application

## 1. ROLE

You are the lead software architect, machine-learning engineer, Python backend engineer, Vue 3 frontend engineer, database engineer, Windows desktop application engineer, DevOps engineer, and code reviewer for this project.

I currently have a working FIFA World Cup / international football match prediction system implemented in a Google Colab `.ipynb` notebook.

The notebook contains the actual data preprocessing, historical feature engineering, model training, model evaluation, model selection, and prediction logic used in my Data Mining project.

I now want to transform this prototype into a real software project with TWO different distribution formats:

### Version A — Web Application

A browser-based web application using:

- Vue 3
- Vite
- Python
- FastAPI
- MySQL
- scikit-learn

### Version B — Windows Desktop Application

A portable Windows application distributed similarly to projects on GitHub Releases.

The user should be able to:

1. Download a ZIP package.
2. Extract it.
3. Run the application.
4. Use the FIFA prediction system.
5. Upload/update datasets.
6. Make predictions.
7. Manage datasets and models.

The desktop version should NOT require Google Colab, Jupyter Notebook, Python installation, Node.js installation, or MySQL installation.

The final goal is to create a professional dual-platform FIFA football prediction application rather than simply converting the Colab notebook into a website.

------

# 2. MOST IMPORTANT RULE — EXISTING NOTEBOOK IS THE SOURCE OF TRUTH

Before writing or modifying implementation code, you MUST completely inspect the existing `.ipynb`, `.py` files, dataset files, and relevant project documentation.

The existing notebook is the authoritative source for the current machine-learning methodology.

Do NOT guess the existing implementation.

Do NOT replace the existing methodology with a theoretically "better" approach unless I explicitly approve it.

Do NOT silently change:

- target definition
- class labels
- feature definitions
- feature engineering
- historical window size
- chronological ordering
- leakage-prevention logic
- preprocessing
- tournament transformation
- neutral venue handling
- train/test split
- model hyperparameters
- model selection criteria
- prediction probability logic

If anything is unclear:

STOP.

Explain the ambiguity to me.

Ask for clarification.

Do NOT invent an implementation.

------

# 3. FIRST TASK — COMPLETE PROJECT AUDIT

Before implementing anything, inspect all existing project files.

The first stage must NOT generate the final application.

First analyze:

## A. Existing Notebook

Identify every important phase/cell.

For example:

- dataset loading
- data auditing
- missing-value handling
- duplicate checking
- completed-match separation
- feature engineering
- leakage prevention
- target construction
- feature encoding
- feature matrix creation
- train/test split
- Logistic Regression
- Decision Tree
- Random Forest
- evaluation
- model selection
- prediction

## B. Existing Python Code

Determine:

- reusable functions
- hardcoded paths
- global variables
- Colab-specific dependencies
- notebook-only state
- duplicated logic
- functions that should become production modules

## C. Existing Dataset

Determine:

- exact columns
- data types
- row count
- date range
- target-related fields
- categorical fields
- missing-value structure
- duplicate structure
- score structure
- tournament structure

## D. Existing Final Model

Identify EXACTLY:

- model type
- hyperparameters
- feature columns
- target classes
- training process
- probability output
- model serialization requirements

## E. Existing Prediction Workflow

Determine exactly which user inputs are required.

Do not assume the user needs:

- host country
- tournament
- venue
- neutral venue
- date

unless the current notebook actually uses them.

------

# 4. TARGET ARCHITECTURE

The final repository should support BOTH:

## Web Application

```text
Browser
   ↓
Vue 3
   ↓
FastAPI
   ↓
Shared ML Core
   ↓
MySQL
```

## Windows Desktop Application

```text
Windows User
   ↓
Electron Desktop Shell
   ↓
Vue 3
   ↓
Bundled FastAPI Executable
   ↓
Shared ML Core
   ↓
SQLite
```

The two versions must share as much code as reasonably possible.

The ML logic must NOT be duplicated.

The dataset validation logic must NOT be duplicated.

The feature engineering logic must NOT be duplicated.

The prediction logic must NOT be duplicated.

Only platform-specific infrastructure should differ.

------

# 5. SHARED CORE ARCHITECTURE

Create a shared Python ML/core layer.

Suggested structure:

```text
core/
├── preprocessing/
├── feature_engineering/
├── models/
├── prediction/
├── dataset/
├── validation/
└── schemas/
```

This shared core should contain:

- data cleaning
- dataset validation
- feature engineering
- leakage prevention
- model training
- model loading
- prediction
- probability calculation
- model evaluation
- dataset version validation

The Web backend and Desktop backend should both call this same core.

The goal is:

```text
Same Dataset
+
Same Features
+
Same Model
+
Same Input
=
Same Prediction
```

regardless of whether the user is using the Web or Desktop version.

------

# 6. WEB VERSION

The web application should use:

### Frontend

- Vue 3
- Vite
- Vue Router
- Pinia where appropriate
- reusable components

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic where appropriate

### Database

- MySQL

Suggested architecture:

```text
web/
├── frontend/
└── backend/
```

The browser must never directly access MySQL.

The architecture must be:

```text
Vue
 ↓
FastAPI
 ↓
Service Layer
 ↓
Repository Layer
 ↓
MySQL
```

------

# 7. WINDOWS DESKTOP VERSION

The Windows version must be designed as a portable application.

The target user experience is:

```text
Download:
FIFA-Prediction-Windows-x64.zip

↓

Extract

↓

Run:
FIFA-Prediction.exe

↓

Application opens

↓

User can immediately make predictions
```

The user should NOT need:

- Python
- pip
- Node.js
- npm
- MySQL
- Git
- Google Colab
- Jupyter

installed separately.

------

# 8. DESKTOP TECHNOLOGY

Use:

### Frontend

Vue 3 + Vite

### Desktop Shell

Electron

### Backend

FastAPI bundled as a standalone Windows executable.

For example:

```text
Electron
   ↓
Vue frontend
   ↓
Bundled FastAPI.exe
   ↓
Shared Python ML Core
```

Use PyInstaller or another appropriate packaging mechanism to bundle the Python backend.

The Electron application should start and stop the bundled FastAPI process automatically.

The user should not see or manually manage the Python backend.

------

# 9. DESKTOP DATABASE

Do NOT require MySQL for the portable Windows version.

Use:

**SQLite**

for the desktop version.

Reason:

The desktop release should be self-contained and portable.

The user should not have to install or configure a database server.

The database should be stored inside the application's user-data directory rather than inside a protected installation directory.

For example:

```text
%APPDATA%/FIFA-Prediction/
```

or an equivalent application data directory.

The database should survive application updates.

------

# 10. DATABASE ABSTRACTION

The Web and Desktop versions must use a common repository/service abstraction.

Example:

```text
Service Layer
      ↓
Repository Interface
      ↓
 ┌───────────────┬───────────────┐
 │               │               │
MySQL Repository SQLite Repository
 │               │
Web              Desktop
```

The business logic must NOT contain SQL specific to one database engine.

This allows:

```text
Web:
MySQL

Desktop:
SQLite
```

while keeping the same application logic.

------

# 11. BUILT-IN DATASET — MUST BE PROTECTED

The application must include an original built-in dataset.

This dataset is the official baseline dataset used by the project.

It MUST be:

- read-only
- protected
- never overwritten
- never deleted through the UI
- never modified by user uploads

The application should clearly identify it as:

> Built-in Dataset — Protected

The UI must NOT show:

- Edit
- Delete
- Overwrite

actions for the built-in dataset.

------

# 12. USER DATASET SYSTEM

Users must be able to upload newer datasets.

However:

```text
User Upload
≠
Built-in Dataset
```

A user upload must always create a new dataset version.

Example:

```text
Built-in Dataset
    └── builtin_v1

User Upload
    └── user_v1

New Upload
    └── user_v2
```

Never:

```text
user_upload → overwrite builtin_v1
```

------

# 13. DATASET VERSIONING

Every dataset must have:

- ID
- name
- version
- source
- type
- creation time
- upload time
- row count
- schema version
- validation status
- active/inactive status
- built-in/user status

Every trained model must remember exactly which dataset version was used.

For example:

```text
Model v3
↓
Dataset user_v2
↓
Feature Version v1
```

------

# 14. DATASET VALIDATION

Before a user dataset can be activated, validate it against the actual notebook schema.

Validation should include, where applicable:

- required columns
- column names
- data types
- date validity
- missing values
- duplicates
- score validity
- team names
- tournament values
- neutral venue values
- invalid rows
- schema compatibility

If the dataset is invalid:

DO NOT activate it.

Provide a clear error message.

Example:

```text
Dataset validation failed.

Missing required column:
home_score
```

Do not silently change the uploaded dataset.

------

# 15. DATASET UPDATE WORKFLOW

The workflow should be:

```text
User uploads CSV
        ↓
Create new dataset version
        ↓
Validate dataset
        ↓
Show validation report
        ↓
User chooses Activate
        ↓
Dataset becomes active
        ↓
User optionally trains a new model
        ↓
New model version created
        ↓
User can use new model for predictions
```

The built-in dataset remains untouched.

------

# 16. MODEL VERSIONING

Every trained model must have:

- model ID
- model type
- model version
- dataset version
- feature version
- training timestamp
- metrics
- model artifact path
- active/inactive status

Example:

```text
Decision Tree
Model v4

Dataset:
user_v2

Features:
feature_v1

Macro F1:
0.xxxx

Created:
2026-08-24
```

------

# 17. FINAL MODEL

The current project selected:

**Decision Tree**

as the final prediction model.

Use the exact Decision Tree implementation and hyperparameters from the existing notebook.

Do NOT replace it during migration.

Logistic Regression and Random Forest may remain available for:

- comparison
- experimentation
- retraining

but the default production model should remain the validated Decision Tree unless I explicitly approve a change.

------

# 18. PREDICTION SYSTEM

The user should be able to make a prediction through BOTH interfaces.

Example:

```text
Home Team:
[ England ▼ ]

Away Team:
[ Argentina ▼ ]

Host / Venue:
[ ... ]

[ Predict ]
```

Then:

```text
Predicted Outcome Probabilities

Home Win       32.4%
Draw           25.8%
Home Loss      41.8%

Predicted Outcome:
Argentina Win
```

The exact input fields must be determined from the existing notebook.

Do NOT invent additional ML inputs.

------

# 19. PREDICTION API

The Web and Desktop versions should expose the same internal prediction service.

The Web version can expose:

```text
POST /api/predictions
```

The Desktop Electron application can communicate with the locally running FastAPI backend.

Example response:

```json
{
  "home_team": "England",
  "away_team": "Argentina",
  "probabilities": {
    "home_win": 0.324,
    "draw": 0.258,
    "home_loss": 0.418
  },
  "predicted_outcome": "Home Loss",
  "model_version": "dt_v1",
  "dataset_version": "builtin_v1"
}
```

The exact schema must follow the existing notebook's class definitions.

------

# 20. PREDICTION HISTORY

Store prediction records.

Each prediction should contain:

- timestamp
- home team
- away team
- relevant match information
- probabilities
- predicted outcome
- dataset version
- model version

This allows the user to review previous predictions.

------

# 21. WEB APPLICATION PAGES

Create a professional web application with:

## Home

- project overview
- current model
- current dataset
- quick prediction

## Match Prediction

- team selection
- required match information
- probability chart
- predicted outcome

## Dataset Management

- dataset versions
- built-in dataset
- upload dataset
- validation
- activate dataset
- dataset statistics

## Model Management

- model versions
- model performance
- dataset used
- training time
- active model
- train new model

## Prediction History

- previous predictions
- probabilities
- model version
- dataset version
- timestamp

------

# 22. WINDOWS DESKTOP APPLICATION PAGES

The desktop application should provide the same major functions:

- Prediction
- Dataset Management
- Model Management
- Prediction History
- Settings/About

The UI should be adapted to a desktop window rather than simply displaying a browser page.

------

# 23. OFFLINE-FIRST DESKTOP MODE

The Windows desktop application should be capable of making predictions without an internet connection after installation.

The release package should include:

- frontend assets
- bundled FastAPI executable
- trained Decision Tree model
- built-in dataset
- SQLite initialization
- required Python runtime dependencies bundled into the backend executable

Therefore:

```text
Internet connection:
NOT REQUIRED for normal local prediction
```

Internet may only be required if the user wants to download/update a new dataset externally.

------

# 24. DESKTOP DATA STORAGE

Do not store user-generated data inside the installation directory if it can be avoided.

Separate:

## Application Files

```text
Program Files / extracted application folder
```

from:

## User Data

```text
%APPDATA%/FIFA-Prediction/
```

User data should include:

- SQLite database
- uploaded datasets
- model versions
- prediction history
- logs
- configuration

This prevents user data from being lost when the application is updated.

------

# 25. DESKTOP RELEASE PACKAGE

The release should eventually look approximately like:

```text
FIFA-Prediction-Windows-x64/
│
├── FIFA-Prediction.exe
├── resources/
├── backend/
├── models/
├── datasets/
├── frontend/
├── README.txt
└── LICENSE
```

The exact Electron packaging structure may differ.

The user experience is what matters:

```text
Extract ZIP
↓
Run FIFA-Prediction.exe
↓
Application starts
```

------

# 26. PORTABLE RELEASE

The preferred release format is:

```text
FIFA-Prediction-Windows-x64.zip
```

No traditional installer is required initially.

Later, an optional installer can be added.

The ZIP release should be suitable for GitHub Releases.

------

# 27. WEB DEPLOYMENT

The Web version should be deployable independently.

Suggested production architecture:

```text
Internet
   ↓
Web Server / Reverse Proxy
   ↓
Vue 3
   ↓
FastAPI
   ↓
MySQL
   ↓
ML Model
```

Do not require users to install Python or MySQL for the Web version.

------

# 28. SHARED ML MODEL ARTIFACT

The trained model artifact should be reusable by both versions.

Example:

```text
models/
└── decision_tree/
    ├── model.joblib
    ├── metadata.json
    └── feature_schema.json
```

The metadata must describe:

- model version
- dataset version
- feature version
- class labels
- training time
- metrics

------

# 29. CRITICAL MODEL COMPATIBILITY REQUIREMENT

The same model and feature schema must produce equivalent predictions in:

### Colab

and:

### Web

and:

### Windows Desktop

For the same:

- dataset
- model
- feature version
- input

the output should be equivalent within reasonable floating-point tolerance.

------

# 30. COLAB VS PRODUCTION VALIDATION

Before declaring the project complete, test known predictions.

For example:

```text
Input:
England vs Argentina
```

Compare:

```text
Colab prediction

vs

Web prediction

vs

Windows Desktop prediction
```

Compare:

- generated features
- model input
- probabilities
- predicted class

If there is a difference, investigate it.

Do NOT modify the expected result simply to make the systems appear identical.

------

# 31. REMOVE COLAB DEPENDENCIES

The final system must NOT depend on:

- Google Colab
- `/content/`
- Google Drive mounting
- notebook state
- manual cell execution
- hardcoded notebook paths

Convert notebook logic into reusable Python modules.

For example:

```text
Notebook:

PHASE 5.3:
DEFINE LEAKAGE-FREE HISTORICAL FEATURE GENERATOR
```

should become a reusable Python function/module.

Do not blindly convert every notebook cell into a separate Python file.

Refactor according to logical responsibilities.

------

# 32. BACKEND STRUCTURE

Suggested:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── predictions.py
│   │   ├── datasets.py
│   │   ├── models.py
│   │   ├── teams.py
│   │   └── history.py
│   │
│   ├── services/
│   │   ├── prediction_service.py
│   │   ├── dataset_service.py
│   │   ├── model_service.py
│   │   └── feature_service.py
│   │
│   ├── ml/
│   │   ├── preprocessing.py
│   │   ├── feature_engineering.py
│   │   ├── training.py
│   │   ├── prediction.py
│   │   └── model_registry.py
│   │
│   ├── repositories/
│   │   ├── dataset_repository.py
│   │   ├── model_repository.py
│   │   └── prediction_repository.py
│   │
│   ├── schemas/
│   ├── db/
│   ├── core/
│   └── utils/
│
├── tests/
├── requirements.txt
└── README.md
```

Improve this structure if necessary after inspecting the actual project.

------

# 33. FRONTEND STRUCTURE

Suggested:

```text
frontend/
│
├── src/
│   ├── components/
│   │   ├── TeamSelector.vue
│   │   ├── PredictionForm.vue
│   │   ├── PredictionResult.vue
│   │   ├── ProbabilityChart.vue
│   │   ├── DatasetManager.vue
│   │   └── ModelManager.vue
│   │
│   ├── views/
│   │   ├── HomeView.vue
│   │   ├── PredictionView.vue
│   │   ├── DatasetView.vue
│   │   ├── ModelView.vue
│   │   └── HistoryView.vue
│   │
│   ├── services/
│   │   └── api.js
│   │
│   ├── stores/
│   ├── router/
│   ├── assets/
│   ├── App.vue
│   └── main.js
│
└── package.json
```

------

# 34. DESKTOP STRUCTURE

Suggested:

```text
desktop/
│
├── electron/
│   ├── main.js
│   ├── preload.js
│   └── process-manager.js
│
├── build/
├── resources/
├── package.json
└── README.md
```

Electron should:

1. Start the bundled FastAPI executable.
2. Wait until FastAPI is ready.
3. Create the application window.
4. Load the Vue frontend.
5. Shut down FastAPI when the application exits.

Handle backend startup failure gracefully.

------

# 35. DATABASE DESIGN

The exact schema must be finalized after inspecting the existing dataset and ML pipeline.

Conceptually, use:

## datasets

- id
- name
- version
- source
- type
- is_builtin
- is_active
- validation_status
- row_count
- schema_version
- created_at

## matches

- id
- dataset_id
- date
- home_team
- away_team
- home_score
- away_score
- tournament
- city
- country
- neutral

## teams

- id
- name
- normalized_name

## model_versions

- id
- model_type
- dataset_id
- feature_version
- model_path
- metrics
- is_active
- created_at

## predictions

- id
- model_version_id
- dataset_id
- home_team
- away_team
- probabilities
- predicted_outcome
- created_at

The exact fields must follow the actual project.

------

# 36. SECURITY

Implement:

- environment variables
- `.env.example`
- `.gitignore`
- upload validation
- file-size limits
- filename sanitization
- path protection
- API validation
- safe model loading
- no hardcoded credentials

Never commit:

- database passwords
- API keys
- `.env`
- private credentials

------

# 37. TESTING

Test the shared ML core first.

Then test:

## Backend

- health
- prediction
- team listing
- dataset upload
- dataset validation
- dataset activation
- model training
- model loading
- prediction history

## Frontend

- team selection
- prediction
- probability display
- dataset upload
- validation result
- model information
- history

## Desktop

- application startup
- FastAPI startup
- SQLite initialization
- prediction
- dataset upload
- application shutdown
- offline prediction

------

# 38. API DOCUMENTATION

FastAPI should expose:

```text
/docs
/redoc
```

All request and response schemas should be documented.

------

# 39. LOGGING

Implement useful logging for:

- application startup
- backend startup
- model loading
- dataset validation
- model training
- prediction
- errors

Do not expose sensitive information.

Desktop logs should be stored in the user-data directory.

------

# 40. README REQUIREMENTS

The final repository must include a comprehensive README.

It must explain:

## Web Version

- prerequisites
- MySQL setup
- backend setup
- frontend setup
- environment variables
- database migration
- dataset initialization
- model initialization
- running the application

## Desktop Version

- Windows requirements
- downloading release ZIP
- extracting ZIP
- running executable
- application data location
- dataset upload
- model retraining
- troubleshooting

## Development

- project structure
- architecture
- testing
- build process

------

# 41. GITHUB RELEASE REQUIREMENTS

The final project should be suitable for GitHub.

Possible releases:

```text
v1.0.0

Assets:

FIFA-Prediction-Windows-x64.zip
Source-code.zip
```

The GitHub Release description should explain:

- features
- supported platform
- installation
- dataset management
- model information
- known limitations

------

# 42. DEVELOPMENT STRATEGY

Do NOT build everything at once.

Use these stages.

## STAGE 0 — COMPLETE INSPECTION

Inspect:

- `.ipynb`
- `.py`
- CSV dataset
- report
- existing project files

Do NOT modify implementation.

Produce:

1. Existing ML pipeline
2. Feature list
3. Dataset schema
4. Model configuration
5. Prediction workflow
6. Current problems
7. Proposed architecture
8. Migration plan

Then STOP.

WAIT FOR MY APPROVAL.

------

## STAGE 1 — EXTRACT SHARED ML CORE

Convert the notebook into reusable Python modules.

Verify:

```text
Notebook
=
Shared ML Core
```

for known test cases.

------

## STAGE 2 — DATABASE ABSTRACTION

Implement:

```text
Repository Interface
        ↓
 ┌──────────────┐
 │              │
MySQL         SQLite
```

Test both.

------

## STAGE 3 — FASTAPI BACKEND

Implement the common API/service layer.

------

## STAGE 4 — WEB VERSION

Implement:

Vue 3
+
FastAPI
+
MySQL

------

## STAGE 5 — DESKTOP VERSION

Implement:

Vue 3
+
Electron
+
Bundled FastAPI
+
SQLite

------

## STAGE 6 — DATASET MANAGEMENT

Implement:

- upload
- validation
- versioning
- activation
- protection of built-in dataset

------

## STAGE 7 — MODEL MANAGEMENT

Implement:

- training
- model versioning
- model activation
- metrics
- model metadata

------

## STAGE 8 — PREDICTION HISTORY

Implement prediction storage and display.

------

## STAGE 9 — CROSS-PLATFORM VALIDATION

Compare:

```text
Colab
Web
Windows Desktop
```

using identical inputs.

------

## STAGE 10 — RELEASE

Build:

```text
FIFA-Prediction-Windows-x64.zip
```

Test it on a clean Windows environment where Python, Node.js, and MySQL are NOT installed.

The application must still run.

------

# 43. FINAL ACCEPTANCE CRITERIA

The project is complete only when all of the following are true:

### Machine Learning

- Existing notebook logic preserved
- Feature engineering preserved
- Temporal leakage prevention preserved
- Decision Tree preserved
- Prediction probabilities match the original system

### Web

- Vue 3 works
- FastAPI works
- MySQL works
- Dataset upload works
- Dataset validation works
- Built-in dataset protected
- Model management works
- Prediction works

### Desktop

- Windows executable works
- No Python installation required
- No Node.js installation required
- No MySQL installation required
- SQLite works
- Built-in dataset protected
- Dataset upload works
- Prediction works offline

### Reproducibility

Every prediction identifies:

- dataset version
- model version
- feature version
- timestamp

### Cross-platform consistency

The same input should produce equivalent predictions in:

- Colab
- Web
- Windows Desktop

------

# 44. IMPORTANT DEVELOPMENT RULE

Do not make large architectural decisions silently.

If you discover a conflict between:

- the existing notebook
- the dataset
- the requested architecture
- the proposed implementation

STOP and explain the conflict.

Ask me before changing the ML methodology.

The priority order is:

1. Preserve validated ML logic.
2. Preserve data correctness.
3. Preserve reproducibility.
4. Protect the built-in dataset.
5. Maintain shared code between Web and Desktop.
6. Keep the architecture maintainable.
7. Improve UI and user experience.

------

# 45. START NOW

Your first response must NOT contain implementation code.

Perform:

**STAGE 0 — COMPLETE INSPECTION**

Read and analyze the existing project files completely.

Then provide:

1. Current project analysis
2. Current ML pipeline
3. Current feature list
4. Dataset schema
5. Current model configuration
6. Current prediction workflow
7. Problems that must be refactored
8. Proposed dual-platform architecture
9. Web architecture
10. Windows architecture
11. Database strategy
12. Shared-core strategy
13. Dataset versioning strategy
14. Model versioning strategy
15. Migration risks
16. Step-by-step implementation plan

Then STOP and wait for my approval.

Do NOT start creating the frontend, backend, database, Electron project, or changing the notebook until I approve the Stage 0 analysis.

------

# 中文说明 / 中文翻译

## 1. 项目目标

我目前有一个只能在 Google Colab `.ipynb` 中运行的 FIFA World Cup / International Football Match Prediction 项目。

现在我要把它升级成为一个真正的软件项目，并且最终提供两种使用形式：

### 版本 A：Web 网站版

技术栈：

- Vue 3
- Vite
- Python
- FastAPI
- MySQL
- scikit-learn

用户通过浏览器访问网站。

------

### 版本 B：Windows 软件版

类似 GitHub 上其他开源项目的 Release。

用户下载：

```text
FIFA-Prediction-Windows-x64.zip
```

然后：

```text
解压
↓
运行 FIFA-Prediction.exe
↓
直接使用
```

不要求用户另外安装：

- Python
- Node.js
- npm
- MySQL
- Git
- Google Colab
- Jupyter

------

# 2. 两个版本不是两个完全不同的项目

核心思想是：

```text
                FIFA Prediction Core
                       │
          ┌────────────┴────────────┐
          │                         │
       Web版本                   Windows版本
          │                         │
       Vue 3                    Vue 3
          │                         │
      FastAPI                  Electron
          │                         │
        MySQL             打包后的 FastAPI
                                    │
                                  SQLite
```

也就是说：

**机器学习代码尽可能只写一份。**

下面这些应该共用：

- Data Cleaning
- Data Validation
- Feature Engineering
- Historical Features
- Leakage Prevention
- Model Training
- Model Loading
- Prediction
- Prediction Probability
- Dataset Validation

不要为了 Web 和 Desktop 分别重新写两套机器学习代码。

------

# 3. 为什么 Desktop 不继续使用 MySQL？

这是这个项目架构中非常重要的一点。

网站：

```text
Vue
↓
FastAPI
↓
MySQL
```

非常合理。

但是 Windows ZIP：

```text
下载ZIP
↓
解压
↓
运行EXE
```

如果要求用户：

```text
安装 MySQL
↓
创建数据库
↓
设置用户名
↓
设置密码
↓
修改配置
```

那么就已经不是一个真正方便的 Portable Application 了。

所以建议：

### Web

使用：

> MySQL

### Windows Desktop

使用：

> SQLite

而且两者通过 Repository Layer 隔离：

```text
Service Layer
       ↓
Repository Interface
       ↓
 ┌─────────┬─────────┐
MySQL    SQLite
```

这样业务逻辑和 ML 逻辑仍然保持一致。

------

# 4. Windows 软件为什么使用 Electron？

因为你的前端已经决定使用 Vue 3。

最自然的 Desktop 架构就是：

```text
Vue 3
↓
Electron
↓
FastAPI.exe
↓
Python ML Core
↓
SQLite
```

Electron 本身会负责：

- 创建 Windows 窗口
- 加载 Vue
- 启动 FastAPI
- 关闭 FastAPI
- 管理 Desktop 生命周期

Python FastAPI 则被打包成：

> ```
> FastAPI.exe
> ```

这样用户完全感觉不到 Python Backend 的存在。

------

# 5. 用户更新数据集

你提出的要求：

> 用户可以更新数据集，但是不能修改原始内置数据集。

Prompt 已经专门设计成：

```text
Built-in Dataset
    ↓
builtin_v1
    ↓
永久只读
```

用户上传：

```text
user_v1
```

再次上传：

```text
user_v2
```

绝对不允许：

```text
user upload
↓
覆盖 builtin_v1
```

------

# 6. 数据集和模型版本绑定

这一点我特别建议保留。

例如：

```text
Dataset
user_v2

        ↓

Decision Tree
Model v4

        ↓

Prediction
England vs Argentina
```

以后用户看到预测结果时可以知道：

```text
Dataset:
user_v2

Model:
Decision Tree v4

Feature Version:
feature_v1

Prediction:
Argentina Win
```

这样整个系统会比普通的“输入球队→输出结果”专业很多。

------

# 7. Desktop 必须支持离线预测

Windows 版本最终应该做到：

```text
下载
↓
解压
↓
运行
↓
预测
```

即使没有网络，也可以：

- 选择球队
- 生成特征
- 加载 Decision Tree
- 预测胜率

网络只在用户需要下载新的数据集时才需要。

------

# 8. 最重要的开发顺序

不要让 Claude 一开始就创建：

```text
frontend/
backend/
database/
electron/
```

第一步必须：

> **完整读取你现有的 `.ipynb` 和 dataset。**

然后告诉你：

```text
你现在的 Colab 是怎么工作的
↓
有哪些 features
↓
Decision Tree 怎么训练
↓
Prediction 怎么生成
↓
哪些代码可以复用
↓
哪些地方必须重构
↓
Web 怎么做
↓
Desktop 怎么做
```

然后**停下来等待你的批准**。

这样可以避免 Claude 在还没理解你们原来的 Data Mining 模型之前就自己“优化”算法。

------

# 9. 最终项目理想状态

最终 GitHub Repository 可以类似：

```text
FIFA-World-Cup-Prediction/
│
├── frontend/
│
├── backend/
│
├── core/
│
├── desktop/
│
├── database/
│
├── datasets/
│
├── models/
│
├── tests/
│
├── docs/
│
├── .env.example
├── .gitignore
└── README.md
```

然后 GitHub Releases：

```text
Releases
│
└── v1.0.0
    │
    ├── FIFA-Prediction-Windows-x64.zip
    └── Source-Code.zip
```

用户下载：

```text
FIFA-Prediction-Windows-x64.zip
```

解压：

```text
FIFA-Prediction-Windows-x64/
    └── FIFA-Prediction.exe
```

双击：

> **直接运行 FIFA Prediction。**

------

# 10. 最终目标

你最终不是在做：

> “把我的 Colab notebook 变成网页。”

而是在做：

> **一个拥有 Web Edition 和 Windows Desktop Edition 的完整 FIFA Football Prediction Application。**

两种版本共享：

**Data → Feature Engineering → Model → Prediction**

但是使用不同的运行环境：

```text
                    Shared ML Core
                          │
              ┌───────────┴───────────┐
              │                       │
          Web Edition          Windows Edition
              │                       │
        Vue + FastAPI          Vue + Electron
              │                       │
            MySQL                  SQLite
              │                       │
          Browser                  EXE
```

最终做到：

> **同一个模型、同一个 Feature Engineering、同一个 Dataset Version，在 Web 和 Windows Desktop 上产生一致的预测结果。**
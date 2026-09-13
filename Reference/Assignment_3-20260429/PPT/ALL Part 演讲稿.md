# ALL Part 演讲稿

## Q1 — Introduction & Purpose（约30秒）

Good morning everyone. Today our group will present **Machine Learning-Based Prediction of FIFA World Cup Match Results**. Football matches are influenced by many factors, but historical match records contain valuable patterns. Our objective is to predict **Home Win, Draw, or Away Win** by using machine learning models. We hope to show that **data mining can support match analysis**, although it cannot guarantee exact results.大家早上好。今天，我们小组将展示基于机器学习的国际足联世界杯比赛结果预测方法。足球比赛的结果受诸多因素影响，但历史比赛数据中蕴含着有价值的规律。我们的目标是利用机器学习模型来预测主队获胜、平局或客队获胜的结果。我们希望证明，尽管数据挖掘无法保证预测的绝对准确性，但它仍然可以辅助比赛分析工作。

------

## Q2 — Description of Data（约30秒）

Our dataset contains **49,477 international football matches** from **1872 to 2026**. Each record includes the match date, home and away teams, scores, tournament, location, and whether the match was played at a neutral venue. Only completed matches were used for model training, while future fixtures were reserved for final prediction. This dataset provides a long historical record for building reliable predictive models.我们的数据集包含了 1872 年至 2026 年间共 49,477 场国际足球比赛的信息。每条记录都包含比赛日期、主队和客队、比分、比赛赛事类型、比赛地点，以及比赛是否在中立场地进行。只有那些已经结束的比赛被用于模型训练，而未来的比赛则被保留下来以用于最终的预测分析。这一数据集为构建可靠的预测模型提供了宝贵的历史数据支持。

------

## Q3 — Data Problems & Pre-processing（约30秒）

Before training the models, we performed several preprocessing steps. First, we sorted all matches chronologically to prevent **data leakage**. Then, we grouped tournament categories, generated the match outcomes, and created **23 engineered features**, such as recent win rate, draw rate, goals scored, and goal difference. Finally, we handled cold-start teams, encoded categorical variables, and validated that all predictor values were complete.在训练模型之前，我们进行了几项预处理工作。首先，我们按时间顺序对所有比赛结果进行了排序，以避免数据泄露问题。接着，我们对各种比赛类型进行了分类，确定了比赛结果，并创建了 23 个用于分析的指标，比如近期胜率、平局率、进球数和净胜球数。最后，我们还处理了那些没有历史数据的球队，对分类变量进行了编码处理，并确认了所有预测指标都是完整的。

------

## Q4 — Data Mining Techniques（约30秒）

We compared **three supervised machine learning models**: Logistic Regression, Decision Tree, and Random Forest. Logistic Regression provides a simple and interpretable baseline. Decision Tree captures non-linear relationships between features, while Random Forest improves robustness through ensemble learning. All three models were trained using the same feature set to ensure a fair comparison.我们比较了三种监督式机器学习模型：逻辑回归、决策树和随机森林。逻辑回归是一种简单且易于理解的基准模型。决策树能够捕捉特征之间的非线性关系，而随机森林则通过集成学习提升了模型的稳定性。为了确保公平比较，这三种模型都是使用相同的特征集进行训练的。

------

## Q5 — Model Validation（约30秒）

To evaluate model performance, we used a **chronological train-test split** and compared multiple evaluation metrics, including Accuracy, Macro Precision, Macro Recall, and Macro F1-score. Although Random Forest achieved the highest overall accuracy, **Decision Tree obtained the highest World Cup Macro F1-score of 0.3903** and was the only model that could meaningfully recognize draw outcomes. Therefore, Decision Tree was selected as our final model.为了评估模型的性能，我们采用了按时间顺序划分的训练集和测试集，并比较了多种评估指标，包括准确率、宏观精确度、宏观召回率以及宏观 F1 分数。虽然随机森林的整体准确率最高，但决策树在世界杯相关数据的评估中取得了 0.3903 的宏观 F1 分数，这一成绩是所有模型中最高的。此外，决策树是唯一能够准确识别平局结果的模型。因此，我们最终选择了决策树作为最优模型。

------

## Q6 — Conclusion & Future Improvements（约30秒）

In conclusion, historical football data provides useful information for predicting match outcomes, but football remains difficult to predict because of factors such as tactics, injuries, and player conditions. Decision Tree achieved the most balanced performance in our project. In future work, we plan to include richer contextual information, optimize model parameters, explore stronger ensemble methods such as XGBoost, and improve draw prediction through better handling of class imbalance.总之，历史足球数据有助于预测比赛结果。不过，由于战术安排、球员伤病状况等因素的影响，足球比赛的结局仍然难以准确预测。在我们的研究中，决策树模型的表现最为出色。在未来的工作中，我们计划引入更多相关的背景信息，优化模型参数，尝试使用更有效的集成学习方法，比如 XGBoost。同时，我们还将通过更好地处理类别不平衡问题来提高平局预测的准确性。
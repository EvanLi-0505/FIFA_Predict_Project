<script setup>
import { ref } from 'vue'

const emit = defineEmits(['accept'])

const scrolledToBottom = ref(false)
const agreed = ref(false)

function handleScroll(event) {
  const el = event.target
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 12) {
    scrolledToBottom.value = true
  }
}

function handleStart() {
  if (!scrolledToBottom.value) {
    window.alert(
      'Please scroll down and finish reading the full disclaimer before continuing.\n\n' +
        '请先完整阅读并滚动至免责声明底部，然后再继续。',
    )
    return
  }
  if (!agreed.value) {
    window.alert(
      'You must check "I have read and agree" before you can continue.\n\n' +
        '您必须勾选"我已阅读并同意"才能继续。',
    )
    return
  }
  emit('accept')
}
</script>

<template>
  <div class="disclaimer-overlay">
    <div class="disclaimer-card">
      <h1>FIFA World Cup Match Prediction</h1>
      <p class="credit">Design by LIZHE</p>

      <div class="disclaimer-text" @scroll="handleScroll">
        <h3>Disclaimer / 免责声明</h3>

        <h4>1. Nature of Predictions / 预测性质</h4>
        <p>
          This application generates match outcome predictions (Home Win / Draw /
          Home Loss) using a machine learning model trained on historical
          international football results. All outputs — including probabilities,
          confidence scores, and team "power ratings" — are statistical estimates
          derived from past data. They are <strong>not</strong> guarantees,
          forecasts, or professional assessments of any future match, team, or
          player. Football outcomes are influenced by countless real-world factors
          (injuries, weather, referee decisions, team morale, tactics, and pure
          chance) that this model does not and cannot account for.
        </p>
        <p>
          本应用使用基于历史国际足球比赛数据训练的机器学习模型生成比赛结果预测（主队胜/平局/主队负）。所有输出内容——包括概率、置信度和球队"实力评分"——均为基于历史数据的统计估计，
          <strong>并非</strong>对任何未来比赛、球队或球员的保证、预言或专业评估。足球比赛结果受伤病、天气、裁判判罚、球队士气、战术安排以及纯粹的运气等无数现实因素影响，本模型无法也不会将这些因素纳入考量。
        </p>

        <h4>2. Not Gambling or Betting Advice / 禁止用于博彩或投注建议</h4>
        <p>
          This application is <strong>not</strong> intended, designed, or licensed
          for use in connection with gambling, sports betting, wagering, or any
          other activity involving real or virtual money based on match outcomes.
          Do not use any prediction, probability, or rating from this application
          as a basis for placing bets or wagers. Sports betting may be illegal in
          your jurisdiction and can cause serious financial and personal harm. If
          you or someone you know has a gambling problem, please seek help from a
          licensed professional or a local support organisation.
        </p>
        <p>
          本应用<strong>不得</strong>用于任何形式的赌博、体育博彩、下注或其他基于比赛结果涉及真实或虚拟货币的活动，也未针对此类用途进行设计或获得相关许可。请勿将本应用提供的任何预测、概率或评分作为下注或投注的依据。体育博彩在您所在的司法管辖区可能属于违法行为，并可能造成严重的经济和个人损害。如果您或您身边的人存在赌博问题，请向持牌专业人士或当地支持机构寻求帮助。
        </p>

        <h4>3. No Official Affiliation / 无官方关联声明</h4>
        <p>
          This project is an independent academic/personal software project. It is
          <strong>not</strong> affiliated with, endorsed by, sponsored by, or
          connected in any way to FIFA, any confederation, national football
          association, league, club, player, or any official football
          organisation. Team names used in this application are used solely for
          descriptive and educational purposes.
        </p>
        <p>
          本项目为独立的学术/个人软件项目，
          <strong>与</strong> FIFA、任何大洲足联、国家足球协会、联赛、俱乐部、球员或任何官方足球组织
          <strong>均无任何关联</strong>，未获得其认可、赞助或授权。本应用中使用的球队名称仅用于描述和教育目的。
        </p>

        <h4>4. Data Accuracy and Limitations / 数据准确性与局限性</h4>
        <p>
          The underlying dataset is sourced from publicly available historical
          match records and may contain inaccuracies, omissions, or errors. Users
          may also upload their own datasets, which are not independently verified
          for accuracy by this application beyond basic structural validation. The
          model's feature set does not include player-level data, injuries,
          suspensions, squad changes, weather, or real-time information. Past
          performance is not a reliable indicator of future results.
        </p>
        <p>
          本应用所使用的基础数据集来源于公开的历史比赛记录，可能存在不准确、遗漏或错误之处。用户也可以上传自己的数据集，本应用除基本的结构性校验外，不对其准确性进行独立核实。模型的特征集不包含球员个人数据、伤病、禁赛、阵容变化、天气或实时信息。过往表现并不能可靠地预示未来结果。
        </p>

        <h4>5. No Liability / 免责条款</h4>
        <p>
          To the fullest extent permitted by applicable law, the developer(s) of
          this application accept <strong>no responsibility or liability</strong>
          for any direct, indirect, incidental, consequential, or other damages —
          including but not limited to financial loss, loss of data, or emotional
          distress — arising from your use of, reliance on, or inability to use
          this application, its predictions, or any information it provides. You
          use this application entirely at your own risk and are solely
          responsible for any decisions you make based on it.
        </p>
        <p>
          在适用法律允许的最大范围内，本应用的开发者<strong>不对</strong>因您使用、依赖或无法使用本应用、其预测结果或其提供的任何信息而产生的任何直接、间接、附带、后果性或其他损害（包括但不限于经济损失、数据丢失或精神损害）承担任何责任。您使用本应用完全自担风险，并对基于本应用做出的任何决定自行负责。
        </p>

        <h4>6. Software Provided "As Is" / 软件按"现状"提供</h4>
        <p>
          This application is provided "as is" and "as available," without
          warranty of any kind, express or implied, including but not limited to
          warranties of merchantability, fitness for a particular purpose, title,
          accuracy, or non-infringement. The developer(s) do not warrant that the
          application will be uninterrupted, error-free, or secure.
        </p>
        <p>
          本应用按"现状"和"现有"状态提供，不附带任何明示或暗示的保证，包括但不限于适销性、特定用途适用性、所有权、准确性或不侵权的保证。开发者不保证本应用将不间断运行、不含错误或绝对安全。
        </p>

        <h4>7. Local Data and Privacy / 本地数据与隐私</h4>
        <p>
          Predictions you make, along with the teams, tournament, and confidence
          scores involved, are stored in this application's own database (locally
          for the desktop edition, or on the server you access for the web
          edition) so that you can review your prediction history. This data is
          not knowingly shared with third parties by the application itself. If
          you download a prediction report, you are responsible for how you store
          or share that file afterward.
        </p>
        <p>
          您所做的预测记录，连同涉及的球队、赛事类型和置信度分数，会存储在本应用自身的数据库中（桌面版存储在本地，网页版存储在您所访问的服务器上），以便您日后查看预测历史。应用本身不会有意将该数据分享给第三方。如果您下载了预测结果报告，您需自行负责该文件之后的存储或分享方式。
        </p>

        <h4>8. Academic / Personal Project Origin / 学术与个人项目性质</h4>
        <p>
          This application originated as a data mining coursework project and has
          been extended into a personal software project. It is provided for
          educational, demonstrational, and entertainment purposes only.
        </p>
        <p>
          本应用最初源自一项数据挖掘课程作业，此后被扩展为个人软件项目，仅供教育、演示和娱乐目的使用。
        </p>

        <h4>9. Age and Appropriate Use / 适用人群</h4>
        <p>
          This application is intended for general audiences interested in
          football statistics. It is not designed for use by young children
          without adult supervision, particularly given the gambling-related
          warnings above.
        </p>
        <p>
          本应用面向对足球数据感兴趣的一般用户。鉴于上述与博彩相关的警示内容，不建议儿童在无成人监督的情况下单独使用本应用。
        </p>

        <h4>10. Changes to This Disclaimer / 免责声明的变更</h4>
        <p>
          This disclaimer may be updated as the application evolves. Continued use
          of the application after an update constitutes acceptance of the revised
          disclaimer.
        </p>
        <p>
          随着应用的更新迭代，本免责声明的内容可能会相应调整。在更新后继续使用本应用即视为您接受修订后的免责声明。
        </p>

        <h4>11. Acknowledgement / 确认声明</h4>
        <p>
          By checking the box below and clicking "Start," you confirm that you
          have read, understood, and agree to every section of this disclaimer in
          full.
        </p>
        <p>
          勾选下方复选框并点击"开始使用"，即表示您确认已完整阅读、理解并同意本免责声明的全部内容。
        </p>
      </div>

      <p v-if="!scrolledToBottom" class="scroll-hint">
        ↓ Scroll to the bottom to continue / 请滚动到底部以继续 ↓
      </p>

      <label class="agree-row" :class="{ disabled: !scrolledToBottom }">
        <input type="checkbox" v-model="agreed" :disabled="!scrolledToBottom" />
        I have read and agree to the disclaimer above / 我已阅读并同意以上免责声明
      </label>

      <button class="start-button" @click="handleStart">Start / 开始使用</button>
    </div>
  </div>
</template>

<style scoped>
.disclaimer-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.disclaimer-card {
  max-width: 720px;
  width: 100%;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 28px 28px 24px;
}

.disclaimer-card h1 {
  margin-bottom: 2px;
  font-size: 1.4rem;
}

.credit {
  color: var(--color-text-muted);
  font-size: 0.82rem;
  margin: 0 0 16px;
}

.disclaimer-text {
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px 18px;
  background: var(--color-surface-raised);
  font-size: 0.85rem;
  line-height: 1.55;
  flex: 1;
  min-height: 0;
}

.disclaimer-text h3 {
  margin-top: 0;
}

.disclaimer-text h4 {
  margin-bottom: 4px;
  color: var(--color-text);
}

.disclaimer-text p {
  margin: 0 0 14px;
  color: var(--color-text-muted);
}

.scroll-hint {
  text-align: center;
  color: var(--color-warning);
  font-size: 0.8rem;
  margin: 10px 0 0;
}

.agree-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 14px 0;
  font-size: 0.88rem;
  cursor: pointer;
}

.agree-row input {
  width: auto;
}

.agree-row.disabled {
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.start-button {
  width: 100%;
  padding: 12px;
  font-size: 1rem;
}
</style>

// Generates a downloadable report for one prediction, as either Markdown
// (.md) or PDF — replacing an earlier self-contained-HTML version per
// user request. Both formats cover the same content: the probability
// breakdown, the model/dataset/confidence stamp, and — when
// `report.comparison` is supplied (see fetchTeamComparisonData) — a
// head-to-head lifetime-record and recent-form comparison of the two
// teams. Both always end with the bilingual "for reference only"
// disclaimer.

import { jsPDF } from 'jspdf'
import { RISK_LEVEL_LABELS, RISK_LEVEL_LABELS_ZH } from './upset'

const OUTCOME_ORDER = ['Home Win', 'Draw', 'Home Loss']
const RISK_COLORS_RGB = { low: [62, 201, 139], medium: [242, 184, 75], high: [240, 87, 107] }
const RATE_CATEGORIES = ['Win rate', 'Draw rate', 'Loss rate']

const OUTCOME_COLORS_RGB = {
  'Home Win': [62, 201, 139],
  Draw: [154, 123, 234],
  'Home Loss': [240, 87, 107],
}
const HOME_COLOR_RGB = [79, 124, 255]
const AWAY_COLOR_RGB = [242, 184, 75]

const DISCLAIMER_EN =
  'This prediction is a statistical estimate generated from historical data and is ' +
  'provided for reference only. It is not a guarantee of any future result and must ' +
  'not be used as a basis for gambling, betting, or wagering of any kind. This ' +
  'application is not affiliated with FIFA or any official football organisation.'

const DISCLAIMER_ZH =
  '本预测结果由历史数据统计生成，仅供参考，不构成对未来比赛结果的保证，' +
  '不得作为任何形式赌博、投注或下注的依据。本应用与 FIFA 或任何官方足球组织均无关联。'

function buildFilenameBase(report, timestamp) {
  const stamp = timestamp.toISOString().slice(0, 19).replace(/[:T]/g, '-')
  return `prediction-${report.homeTeam}-vs-${report.awayTeam}-${stamp}`
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// ---------------------------------------------------------------------
// Markdown
// ---------------------------------------------------------------------

/** @see downloadPredictionReportPdf for the shared `report` shape. */
export function downloadPredictionReportMarkdown(report) {
  const timestamp = report.timestamp ? new Date(report.timestamp) : new Date()

  const lines = []
  lines.push(`# ${report.homeTeam} vs ${report.awayTeam}`)
  lines.push('')
  lines.push(
    `**Host:** ${report.hostCountry}` +
      `  **Tournament:** ${report.tournament}${report.tournamentCategory ? ` (${report.tournamentCategory})` : ''}` +
      `  **Venue:** ${report.neutral ? 'Neutral' : 'Home'}`,
  )
  lines.push(`**Generated:** ${timestamp.toLocaleString()}`)
  lines.push('')
  if (report.upset?.level === 'high') {
    lines.push('> ## ⚠ HIGH-RISK PREDICTION / 高风险预测')
    lines.push(
      `> ${report.upset.underdogTeam} (underdog) has a ${pct(report.upset.probability)} chance of ` +
        `beating ${report.upset.favoriteTeam} outright — above the 30% high-risk threshold.`,
    )
    lines.push('')
  }
  lines.push(`## Predicted outcome: **${report.predictedOutcome}**`)
  lines.push('')
  lines.push('| Outcome | Probability |')
  lines.push('|---|---:|')
  for (const outcome of OUTCOME_ORDER) {
    if (!(outcome in report.probabilities)) continue
    lines.push(`| ${outcome} | ${(report.probabilities[outcome] * 100).toFixed(1)}% |`)
  }
  lines.push('')
  lines.push(
    `**Model:** \`${report.modelVersion}\`  **Dataset:** \`${report.datasetVersion}\`  ` +
      `**Confidence:** ${(report.confidence * 100).toFixed(1)}%`,
  )

  if (report.upset) {
    const { upset } = report
    lines.push('')
    lines.push('## Upset risk / 爆冷风险')
    lines.push('')
    lines.push(
      `**${pct(upset.probability)}** chance that ${upset.underdogTeam} (underdog) beats ` +
        `${upset.favoriteTeam} (favorite) outright — ` +
        `**${RISK_LEVEL_LABELS[upset.level]} / ${RISK_LEVEL_LABELS_ZH[upset.level]}**`,
    )
    lines.push('')
    lines.push('Tiers: Low < 15% · Medium 15–30% · High > 30% (draws are not counted as upsets).')
    if (upset.history) {
      lines.push('')
      lines.push(
        `### Historical upsets (underdog won despite a pre-match chance below ${pct(upset.history.home.max_probability)})`,
      )
      for (const team of [upset.history.home, upset.history.away]) {
        lines.push('')
        lines.push(
          `**${team.team}** — ${team.summary.matches} matches · caused ${team.summary.upsets_caused} · ` +
            `suffered ${team.summary.upsets_suffered}`,
        )
        if (!team.matches.length) continue
        lines.push('')
        lines.push('| Date | Match | Score | Tournament | Pre-match chance | Role |')
        lines.push('|---|---|---|---|---:|---|')
        for (const m of team.matches) {
          lines.push(
            `| ${m.date} | ${m.home_team} vs ${m.away_team} | ${m.home_score}–${m.away_score} | ` +
              `${m.tournament} | ${pct(m.upset_probability)} | ${m.role === 'caused' ? 'Caused' : 'Suffered'} |`,
          )
        }
      }
    }
  }

  if (report.comparison) {
    const { home, away } = report.comparison
    lines.push('')
    lines.push('## Head-to-head: lifetime record')
    lines.push('')
    lines.push('| Team | Win rate | Draw rate | Loss rate |')
    lines.push('|---|---:|---:|---:|')
    lines.push(
      `| ${report.homeTeam} | ${(home.stats.win_rate * 100).toFixed(1)}% | ` +
        `${(home.stats.draw_rate * 100).toFixed(1)}% | ${(home.stats.loss_rate * 100).toFixed(1)}% |`,
    )
    lines.push(
      `| ${report.awayTeam} | ${(away.stats.win_rate * 100).toFixed(1)}% | ` +
        `${(away.stats.draw_rate * 100).toFixed(1)}% | ${(away.stats.loss_rate * 100).toFixed(1)}% |`,
    )

    lines.push('')
    lines.push('## Head-to-head: recent form (goal difference per match, oldest to newest)')
    lines.push('')
    lines.push(`| # | ${report.homeTeam} | ${report.awayTeam} |`)
    lines.push('|---:|---:|---:|')
    const rowCount = Math.max(home.series.length, away.series.length)
    for (let i = 0; i < rowCount; i++) {
      const homeValue = home.series[i] ? formatSigned(home.series[i].value) : '—'
      const awayValue = away.series[i] ? formatSigned(away.series[i].value) : '—'
      lines.push(`| ${i + 1} | ${homeValue} | ${awayValue} |`)
    }
  }

  lines.push('')
  lines.push('---')
  lines.push('')
  lines.push(`*${DISCLAIMER_EN}*`)
  lines.push('')
  lines.push(`*${DISCLAIMER_ZH}*`)

  const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
  triggerDownload(blob, `${buildFilenameBase(report, timestamp)}.md`)
}

function formatSigned(value) {
  return value > 0 ? `+${value}` : `${value}`
}

function pct(value) {
  return `${(value * 100).toFixed(1)}%`
}

// ---------------------------------------------------------------------
// PDF
// ---------------------------------------------------------------------

// jsPDF's built-in fonts (Helvetica/Times/Courier) only support Latin
// text — there is no CJK glyph coverage, so `doc.text()` cannot render
// the Chinese disclaimer directly (embedding a whole CJK font just for
// one paragraph would add megabytes to the bundle). Instead, the Chinese
// text is rasterised to a small PNG using a plain <canvas> — canvas text
// rendering goes through the browser/OS font stack, which already
// handles CJK correctly — and that image is placed into the PDF like any
// other graphic. The English text renders as normal vector PDF text.
function renderTextToPngDataUrl(
  text,
  { fontPx = 20, maxWidthPx = 1400, color = '#6b7394', fontWeight = 'normal' } = {},
) {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  ctx.font = `${fontWeight} ${fontPx}px "Segoe UI", sans-serif`

  // Manual word-wrap: canvas has no built-in text wrapping.
  const words = text.split('')
  const lines = []
  let current = ''
  for (const ch of words) {
    const test = current + ch
    if (ctx.measureText(test).width > maxWidthPx && current) {
      lines.push(current)
      current = ch
    } else {
      current = test
    }
  }
  if (current) lines.push(current)

  const lineHeight = Math.round(fontPx * 1.5)
  canvas.width = maxWidthPx
  canvas.height = lineHeight * lines.length

  ctx.font = `${fontWeight} ${fontPx}px "Segoe UI", sans-serif`
  ctx.fillStyle = color
  ctx.textBaseline = 'top'
  lines.forEach((line, i) => ctx.fillText(line, 0, i * lineHeight))

  return { dataUrl: canvas.toDataURL('image/png'), width: canvas.width, height: canvas.height }
}

/**
 * @param {object} report
 * @param {string} report.homeTeam
 * @param {string} report.awayTeam
 * @param {string} report.hostCountry
 * @param {string} report.tournament
 * @param {string} [report.tournamentCategory]
 * @param {number} report.neutral
 * @param {Record<string, number>} report.probabilities
 * @param {string} report.predictedOutcome
 * @param {number} report.confidence
 * @param {string} report.modelVersion
 * @param {string} report.datasetVersion
 * @param {string|Date} [report.timestamp]
 * @param {object} [report.comparison] Optional head-to-head data (from
 *   `fetchTeamComparisonData`) — when present, the report adds a
 *   win/draw/loss and recent-form comparison between the two teams. Omit
 *   if that data failed to load; the report still works without it.
 * @param {{stats: object, series: Array}} [report.comparison.home]
 * @param {{stats: object, series: Array}} [report.comparison.away]
 * @param {object} [report.upset] `upsetSummary()` output plus optional
 *   `history` (`fetchUpsetHistory`) — adds the upset-risk section, each
 *   team's historical upsets, and the high-risk banner above 30%.
 */
export function downloadPredictionReportPdf(report) {
  const timestamp = report.timestamp ? new Date(report.timestamp) : new Date()
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const marginX = 48
  const pageWidth = doc.internal.pageSize.getWidth()
  const contentWidth = pageWidth - marginX * 2
  let y = 56

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(18)
  doc.text(`${report.homeTeam} vs ${report.awayTeam}`, marginX, y)
  y += 22

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(107, 115, 148)
  const metaLine =
    `Host: ${report.hostCountry}  |  Tournament: ${report.tournament}` +
    `${report.tournamentCategory ? ` (${report.tournamentCategory})` : ''}` +
    `  |  ${report.neutral ? 'Neutral venue' : 'Home venue'}`
  doc.text(metaLine, marginX, y)
  y += 14
  doc.text(`Generated: ${timestamp.toLocaleString()}`, marginX, y)
  y += 26

  if (report.upset?.level === 'high') {
    y = drawHighRiskBanner(doc, report.upset, marginX, y, contentWidth)
  }

  doc.setTextColor(26, 31, 54)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(13)
  doc.text(`Predicted outcome: ${report.predictedOutcome}`, marginX, y)
  y += 20

  y = drawProbabilityBars(doc, report.probabilities, report.predictedOutcome, marginX, y, contentWidth)
  y += 10

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(107, 115, 148)
  doc.text(
    `Model: ${report.modelVersion}   Dataset: ${report.datasetVersion}   ` +
      `Confidence: ${(report.confidence * 100).toFixed(1)}%`,
    marginX,
    y,
  )
  y += 26

  if (report.upset) {
    y = drawUpsetRisk(doc, report.upset, marginX, y, contentWidth)
    y += 16
  }

  if (report.comparison) {
    y = ensureSpace(doc, y, 260)
    y = drawSectionTitle(doc, 'Head-to-head: lifetime record', marginX, y)
    y = drawGroupedBars(doc, report, marginX, y)
    y += 16

    y = drawSectionTitle(doc, 'Head-to-head: recent form (goal difference per match)', marginX, y)
    y = drawLineChart(doc, report, marginX, y, contentWidth)
    y += 10
  }

  if (report.upset?.history) {
    y += 10
    y = drawUpsetHistory(doc, report.upset.history, marginX, y, contentWidth)
  }

  y = ensureSpace(doc, y, 110)
  y += 14
  doc.setDrawColor(230, 233, 242)
  doc.line(marginX, y, pageWidth - marginX, y)
  y += 16

  doc.setFont('helvetica', 'italic')
  doc.setFontSize(8)
  doc.setTextColor(154, 161, 189)
  const wrappedEn = doc.splitTextToSize(DISCLAIMER_EN, contentWidth)
  doc.text(wrappedEn, marginX, y)
  y += wrappedEn.length * 10 + 8

  // Chinese disclaimer — rasterised, see renderTextToPngDataUrl's doc comment.
  const zh = renderTextToPngDataUrl(DISCLAIMER_ZH, { fontPx: 20, maxWidthPx: Math.round(contentWidth * 4) })
  const zhWidthPt = contentWidth
  const zhHeightPt = (zh.height / zh.width) * zhWidthPt
  doc.addImage(zh.dataUrl, 'PNG', marginX, y, zhWidthPt, zhHeightPt)

  doc.save(`${buildFilenameBase(report, timestamp)}.pdf`)
}

const PAGE_TOP_Y = 56
const PAGE_BOTTOM_MARGIN = 48

function ensureSpace(doc, y, needed) {
  if (y + needed <= doc.internal.pageSize.getHeight() - PAGE_BOTTOM_MARGIN) return y
  doc.addPage()
  return PAGE_TOP_Y
}

function drawHighRiskBanner(doc, upset, x, y, width) {
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  const detail = doc.splitTextToSize(
    `${upset.underdogTeam} (underdog) has a ${pct(upset.probability)} chance of beating ` +
      `${upset.favoriteTeam} outright - above the 30% high-risk threshold.`,
    width - 28,
  )
  const height = 34 + detail.length * 11
  doc.setFillColor(...RISK_COLORS_RGB.high)
  doc.roundedRect(x, y, width, height, 4, 4, 'F')

  doc.setTextColor(255, 255, 255)
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(15)
  doc.text('HIGH-RISK PREDICTION', x + 14, y + 20)
  const titleWidth = doc.getTextWidth('HIGH-RISK PREDICTION')

  // Chinese label rasterised like the disclaimer (no CJK glyphs in jsPDF fonts).
  // The image is 1.5x the font size tall with glyphs in the top ~2/3, so a
  // 21pt-tall image gives ~14pt glyphs whose top lines up with the title's caps.
  const zh = renderTextToPngDataUrl('高风险预测', {
    fontPx: 60,
    maxWidthPx: 320,
    color: '#ffffff',
    fontWeight: 'bold',
  })
  const zhHeight = 21
  doc.addImage(zh.dataUrl, 'PNG', x + 22 + titleWidth, y + 7, (zh.width / zh.height) * zhHeight, zhHeight)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.text(detail, x + 14, y + 36)
  return y + height + 18
}

function drawUpsetRisk(doc, upset, x, y, width) {
  y = ensureSpace(doc, y, 90)
  y = drawSectionTitle(doc, 'Upset risk (underdog wins outright)', x, y)

  const [r, g, b] = RISK_COLORS_RGB[upset.level]
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(20)
  doc.setTextColor(r, g, b)
  doc.text(pct(upset.probability), x, y + 14)
  const numberWidth = doc.getTextWidth(pct(upset.probability))

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(26, 31, 54)
  doc.text(
    `${RISK_LEVEL_LABELS[upset.level]}: ${upset.underdogTeam} (underdog) vs ${upset.favoriteTeam} (favorite)`,
    x + numberWidth + 12,
    y + 12,
  )
  y += 26

  // 0-50% scale; underdog win chance can't exceed 50% by definition.
  const barHeight = 8
  doc.setFillColor(230, 233, 242)
  doc.roundedRect(x, y, width, barHeight, 2, 2, 'F')
  doc.setFillColor(r, g, b)
  doc.roundedRect(x, y, width * Math.min(upset.probability / 0.5, 1), barHeight, 2, 2, 'F')
  doc.setDrawColor(107, 115, 148)
  doc.setFontSize(8)
  doc.setTextColor(107, 115, 148)
  for (const [threshold, label] of [[0.15, '15%'], [0.3, '30%']]) {
    const tx = x + width * (threshold / 0.5)
    doc.line(tx, y - 3, tx, y + barHeight + 3)
    doc.text(label, tx, y + barHeight + 12, { align: 'center' })
  }
  doc.text('Low < 15%  |  Medium 15-30%  |  High > 30%', x + width, y + barHeight + 12, { align: 'right' })
  return y + barHeight + 18
}

function drawUpsetHistory(doc, history, x, y, width) {
  y = ensureSpace(doc, y, 60)
  y = drawSectionTitle(
    doc,
    `Historical upsets (underdog won despite a pre-match chance below ${pct(history.home.max_probability)})`,
    x,
    y,
  )

  const columns = [
    { label: 'Date', x: 0 },
    { label: 'Match', x: 58 },
    { label: 'Score', x: 228 },
    { label: 'Chance', x: 262 },
    { label: 'Role', x: 302 },
    { label: 'Tournament', x: 346 },
  ]

  for (const team of [history.home, history.away]) {
    y = ensureSpace(doc, y, 40)
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10)
    doc.setTextColor(26, 31, 54)
    doc.text(
      `${team.team}: ${team.summary.matches} matches, caused ${team.summary.upsets_caused}, ` +
        `suffered ${team.summary.upsets_suffered}`,
      x,
      y,
    )
    y += 14
    if (!team.matches.length) {
      y += 6
      continue
    }

    doc.setFontSize(8)
    doc.setTextColor(107, 115, 148)
    columns.forEach((c) => doc.text(c.label, x + c.x, y))
    y += 11
    doc.setFont('helvetica', 'normal')
    doc.setTextColor(26, 31, 54)
    for (const m of team.matches) {
      y = ensureSpace(doc, y, 12)
      const row = [
        m.date,
        `${m.home_team} vs ${m.away_team}`,
        `${m.home_score}-${m.away_score}`,
        pct(m.upset_probability),
        m.role === 'caused' ? 'Caused' : 'Suffered',
        m.tournament,
      ]
      row.forEach((value, i) => {
        const maxWidth = (columns[i + 1]?.x ?? width) - columns[i].x - 6
        doc.text(doc.splitTextToSize(value, maxWidth)[0], x + columns[i].x, y)
      })
      y += 11
    }
    y += 8
  }
  return y
}

function drawSectionTitle(doc, title, x, y) {
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(26, 31, 54)
  doc.text(title, x, y)
  return y + 16
}

function drawProbabilityBars(doc, probabilities, predictedOutcome, x, y, width) {
  const barHeight = 10
  for (const outcome of OUTCOME_ORDER) {
    if (!(outcome in probabilities)) continue
    const value = probabilities[outcome]
    const pct = (value * 100).toFixed(1)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(10)
    doc.setTextColor(26, 31, 54)
    doc.text(outcome, x, y)
    doc.text(`${pct}%`, x + width, y, { align: 'right' })
    y += 4

    doc.setFillColor(230, 233, 242)
    doc.roundedRect(x, y, width, barHeight, 2, 2, 'F')

    const [r, g, b] = OUTCOME_COLORS_RGB[outcome] ?? HOME_COLOR_RGB
    doc.setFillColor(r, g, b)
    doc.setGState(new doc.GState({ opacity: outcome === predictedOutcome ? 1 : 0.55 }))
    doc.roundedRect(x, y, width * value, barHeight, 2, 2, 'F')
    doc.setGState(new doc.GState({ opacity: 1 }))

    y += barHeight + 14
  }
  return y
}

function drawGroupedBars(doc, report, x, y) {
  const { home, away } = report.comparison
  const homeValues = [home.stats.win_rate, home.stats.draw_rate, home.stats.loss_rate]
  const awayValues = [away.stats.win_rate, away.stats.draw_rate, away.stats.loss_rate]

  drawLegend(doc, report.homeTeam, HOME_COLOR_RGB, report.awayTeam, AWAY_COLOR_RGB, x, y)
  y += 14

  const barMaxHeight = 70
  const barWidth = 16
  const groupGap = 90
  const chartTop = y

  RATE_CATEGORIES.forEach((category, i) => {
    const groupX = x + i * groupGap
    const homeH = homeValues[i] * barMaxHeight
    const awayH = awayValues[i] * barMaxHeight

    doc.setFillColor(...HOME_COLOR_RGB)
    doc.rect(groupX, chartTop + (barMaxHeight - homeH), barWidth, homeH, 'F')
    doc.setFillColor(...AWAY_COLOR_RGB)
    doc.rect(groupX + barWidth + 4, chartTop + (barMaxHeight - awayH), barWidth, awayH, 'F')

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(9)
    doc.setTextColor(107, 115, 148)
    doc.text(category, groupX, chartTop + barMaxHeight + 14)
  })

  return chartTop + barMaxHeight + 24
}

function drawLegend(doc, homeLabel, homeRgb, awayLabel, awayRgb, x, y) {
  doc.setFontSize(9)
  doc.setFont('helvetica', 'normal')

  doc.setFillColor(...homeRgb)
  doc.circle(x + 3, y - 3, 3, 'F')
  doc.setTextColor(107, 115, 148)
  doc.text(homeLabel, x + 10, y)

  const homeLabelWidth = doc.getTextWidth(homeLabel)
  const awayX = x + 10 + homeLabelWidth + 20
  doc.setFillColor(...awayRgb)
  doc.circle(awayX - 7, y - 3, 3, 'F')
  doc.text(awayLabel, awayX, y)
}

function drawLineChart(doc, report, x, y, width) {
  const { home, away } = report.comparison
  const height = 90

  drawLegend(doc, report.homeTeam, HOME_COLOR_RGB, report.awayTeam, AWAY_COLOR_RGB, x, y)
  y += 14

  const allValues = [...home.series, ...away.series].map((p) => Math.abs(p.value))
  const maxAbs = Math.max(1, ...allValues)
  const zeroY = y + height / 2

  doc.setDrawColor(230, 233, 242)
  doc.setLineDashPattern([2, 2], 0)
  doc.line(x, zeroY, x + width, zeroY)
  doc.setLineDashPattern([], 0)

  function plot(series, rgb) {
    if (series.length < 2) return
    doc.setDrawColor(...rgb)
    doc.setLineWidth(1.5)
    for (let i = 0; i < series.length - 1; i++) {
      const x1 = x + (i / (series.length - 1)) * width
      const x2 = x + ((i + 1) / (series.length - 1)) * width
      const y1 = zeroY - (series[i].value / maxAbs) * (height / 2)
      const y2 = zeroY - (series[i + 1].value / maxAbs) * (height / 2)
      doc.line(x1, y1, x2, y2)
    }
  }

  plot(home.series, HOME_COLOR_RGB)
  plot(away.series, AWAY_COLOR_RGB)

  return y + height + 4
}

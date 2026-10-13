const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

const C = {
  navy: "1B3A5C",
  navyDark: "152E4A",
  gold: "D4A843",
  white: "FFFFFF",
  offWhite: "F5F6F8",
  lightGray: "E8ECF0",
  midGray: "8C9AAE",
  darkText: "1E2D3D",
  bodyText: "333333",
  blue: "2E75B6",
  lightBlue: "5B9BD5",
  teal: "0D9488",
};

const FONT_HEADER = "Trebuchet MS";
const FONT_BODY = "Calibri";
const TOTAL = 20;

async function iconToBase64Png(IconComponent, color = "#000000", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

function addHeaderBar(slide, pres, title) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.68,
    fill: { color: C.navy },
  });
  slide.addText(title, {
    x: 0.45, y: 0, w: 9.1, h: 0.68,
    fontSize: 15, fontFace: FONT_HEADER, color: C.white,
    bold: true, valign: "middle", margin: 0, charSpacing: 1.2,
  });
}

function addGoldStripe(slide, pres) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.08, h: 5.625,
    fill: { color: C.gold },
  });
}

function addFooter(slide, page) {
  slide.addText("ClimateWise  ·  Glossário e motores matemáticos  ·  Agosto 2026", {
    x: 0.45, y: 5.36, w: 7.7, h: 0.18,
    fontSize: 9, fontFace: FONT_BODY, color: C.midGray, margin: 0,
  });
  slide.addText(page + " / " + TOTAL, {
    x: 8.4, y: 5.36, w: 1.15, h: 0.18,
    fontSize: 9, fontFace: FONT_BODY, color: C.midGray, align: "right", margin: 0,
  });
}

const makeShadow = () => ({ type: "outer", color: "000000", blur: 4, offset: 2, angle: 135, opacity: 0.1 });

function glossTable(slide, rows, y, rowH) {
  const headerOpts = () => ({
    fontSize: 11, fontFace: FONT_BODY, bold: true, color: C.white,
    fill: { color: C.navy }, valign: "middle",
    border: [{ pt: 0.5, color: C.navy }], margin: [3, 5, 3, 5],
  });
  const cell = (alt, bold) => ({
    fontSize: 11, fontFace: FONT_BODY,
    color: bold ? C.navy : C.bodyText, bold: !!bold,
    fill: { color: alt ? C.offWhite : C.white }, valign: "middle",
    border: [{ pt: 0.5, color: C.lightGray }], margin: [3, 5, 3, 5],
  });
  slide.addTable(
    rows.map((row, ri) => {
      if (ri === 0) return row.map((c) => ({ text: c, options: headerOpts() }));
      const alt = ri % 2 === 0;
      return row.map((c, ci) => ({ text: c, options: cell(alt, ci === 0) }));
    }),
    { x: 0.35, y, w: 9.3, colW: [2.15, 4.35, 2.8], rowH: rowH || 0.42 }
  );
}

function whyBox(slide, pres, x, y, w, h, title, body) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: C.offWhite },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.08, h,
    fill: { color: C.gold },
  });
  slide.addText(title, {
    x: x + 0.18, y: y + 0.08, w: w - 0.28, h: 0.28,
    fontSize: 12, fontFace: FONT_HEADER, color: C.navy, bold: true, margin: 0,
  });
  slide.addText(body, {
    x: x + 0.18, y: y + 0.38, w: w - 0.28, h: h - 0.48,
    fontSize: 12, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
  });
}

async function buildPresentation() {
  const {
    FaCity, FaTint, FaCloudRain, FaChartLine, FaMapMarkerAlt,
    FaIndustry, FaWater, FaBook, FaCogs,
  } = require("react-icons/fa");

  const iconCity = await iconToBase64Png(FaCity, "#2E75B6", 256);
  const iconTint = await iconToBase64Png(FaTint, "#2E75B6", 256);
  const iconRain = await iconToBase64Png(FaCloudRain, "#1B3A5C", 256);
  const iconChart = await iconToBase64Png(FaChartLine, "#1B3A5C", 256);
  const iconMap = await iconToBase64Png(FaMapMarkerAlt, "#0D9488", 256);
  const iconIndustry = await iconToBase64Png(FaIndustry, "#1B3A5C", 256);
  const iconWater = await iconToBase64Png(FaWater, "#2E75B6", 256);
  const iconBook = await iconToBase64Png(FaBook, "#D4A843", 256);
  const iconCogs = await iconToBase64Png(FaCogs, "#1B3A5C", 256);

  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "ClimateWise";
  pres.title = "ClimateWise para município e CEDAE — glossário e motores matemáticos";
  pres.subject = "Siglas, nomenclatura e por que cada módulo matemático serve à prefeitura e ao saneamento";

  // 1 TITLE
  {
    const slide = pres.addSlide();
    slide.background = { color: C.navy };
    addGoldStripe(slide, pres);
    slide.addText("CLIMATEWISE", {
      x: 0.55, y: 0.5, w: 6.5, h: 0.32,
      fontSize: 13, fontFace: FONT_BODY, color: C.gold, bold: true, charSpacing: 3, margin: 0,
    });
    slide.addText([
      { text: "MUNICÍPIO, ÁGUA", options: { breakLine: true } },
      { text: "E A MATEMÁTICA", options: { breakLine: true } },
      { text: "QUE JÁ EXISTE", options: {} },
    ], {
      x: 0.55, y: 0.95, w: 6.6, h: 2.15,
      fontSize: 28, fontFace: FONT_HEADER, color: C.white, bold: true, margin: 0,
    });
    slide.addText("Glossário  ·  por que cada modelo  ·  CEDAE e Defesa Civil", {
      x: 0.55, y: 3.3, w: 7.2, h: 0.35,
      fontSize: 15, fontFace: FONT_BODY, color: C.gold, bold: true, margin: 0,
    });
    slide.addShape(pres.shapes.OVAL, {
      x: 7.55, y: 1.15, w: 1.7, h: 1.7,
      fill: { color: C.navyDark },
      line: { color: C.gold, width: 2 },
    });
    slide.addText("CW", {
      x: 7.55, y: 1.45, w: 1.7, h: 1.1,
      fontSize: 28, fontFace: FONT_HEADER, color: C.gold, bold: true,
      align: "center", valign: "middle", margin: 0,
    });
    slide.addShape(pres.shapes.LINE, {
      x: 0.55, y: 4.55, w: 8.9, h: 0,
      line: { color: C.gold, width: 1 },
    });
    slide.addText("Documento de evolução de produto  ·  agosto 2026", {
      x: 0.55, y: 4.7, w: 8.9, h: 0.3,
      fontSize: 13, fontFace: FONT_BODY, color: C.midGray, margin: 0,
    });
  }

  // 2 COMO LER
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "COMO LER ESTA APRESENTAÇÃO");
    addFooter(slide, 2);
    const blocks = [
      { n: "1", t: "Glossário", d: "Siglas, grandezas e nomes matemáticos. Sem isso, LSTM e GEV viram jargão." },
      { n: "2", t: "Família de modelos", d: "Não existe um único modelo para chuva, seca e drenagem. Cada pergunta exige um instrumento." },
      { n: "3", t: "Módulos", d: "Para cada motor: o que é, a situação (prefeitura ou CEDAE) e por que ele — e não o vizinho." },
      { n: "4", t: "Fatos e fontes", d: "Números oficiais do Guandu, Alerta Rio, ANA e INMET. O que acoplar, sem inventar dado." },
    ];
    blocks.forEach((b, i) => {
      const y = 0.9 + i * 1.05;
      slide.addShape(pres.shapes.OVAL, {
        x: 0.5, y: y + 0.15, w: 0.48, h: 0.48, fill: { color: C.navy },
      });
      slide.addText(b.n, {
        x: 0.5, y: y + 0.15, w: 0.48, h: 0.48,
        fontSize: 16, fontFace: FONT_HEADER, color: C.white, bold: true,
        align: "center", valign: "middle", margin: 0,
      });
      slide.addText(b.t, {
        x: 1.2, y: y, w: 8.2, h: 0.35,
        fontSize: 16, fontFace: FONT_HEADER, color: C.navy, bold: true, margin: 0,
      });
      slide.addText(b.d, {
        x: 1.2, y: y + 0.38, w: 8.2, h: 0.5,
        fontSize: 14, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
      });
    });
  }

  // 3 DOIS CLIENTES
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "DUAS PERGUNTAS, O MESMO CLIMA");
    addFooter(slide, 3);
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.4, y: 0.9, w: 4.45, h: 4.2, fill: { color: C.offWhite },
    });
    slide.addImage({ data: iconCity, x: 0.6, y: 1.08, w: 0.36, h: 0.36 });
    slide.addText("Prefeitura / Defesa Civil", {
      x: 1.08, y: 1.08, w: 3.5, h: 0.36,
      fontSize: 15, fontFace: FONT_HEADER, color: C.navy, bold: true, valign: "middle", margin: 0,
    });
    slide.addText("Pergunta: onde e quando o extremo atinge gente e via?", {
      x: 0.6, y: 1.55, w: 4.05, h: 0.55,
      fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
    });
    slide.addText(
      [
        { text: "Alagamento e enchente urbana", options: { bullet: true, breakLine: true } },
        { text: "Deslizamento em encosta", options: { bullet: true, breakLine: true } },
        { text: "Onda de calor e saúde", options: { bullet: true, breakLine: true } },
        { text: "Estiagem e comunicação", options: { bullet: true, breakLine: true } },
        { text: "Drenagem (chuva de 10–100 anos)", options: { bullet: true } },
      ],
      { x: 0.6, y: 2.2, w: 4.05, h: 2.5, fontSize: 14, fontFace: FONT_BODY, color: C.darkText, margin: 0, paraSpaceAfter: 6 }
    );
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 5.15, y: 0.9, w: 4.45, h: 4.2, fill: { color: C.navy },
    });
    slide.addImage({ data: iconTint, x: 5.35, y: 1.08, w: 0.36, h: 0.36 });
    slide.addText("CEDAE / saneamento", {
      x: 5.83, y: 1.08, w: 3.5, h: 0.36,
      fontSize: 15, fontFace: FONT_HEADER, color: C.white, bold: true, valign: "middle", margin: 0,
    });
    slide.addText("Pergunta: o manancial e a ETA aguentam o clima desta semana e desta estação?", {
      x: 5.35, y: 1.55, w: 4.05, h: 0.7,
      fontSize: 13, fontFace: FONT_BODY, color: C.lightGray, margin: 0,
    });
    slide.addText(
      [
        { text: "Recarga vs. estiagem no Guandu / Paraíba", options: { bullet: true, breakLine: true, color: C.white } },
        { text: "Tratabilidade (turbidez, odor) após extremo", options: { bullet: true, breakLine: true, color: C.white } },
        { text: "Rede de esgoto em chuva forte", options: { bullet: true, breakLine: true, color: C.white } },
        { text: "Alocação sazonal (3–9 meses)", options: { bullet: true, breakLine: true, color: C.white } },
        { text: "Exposição de ETA e adutora", options: { bullet: true, color: C.white } },
      ],
      { x: 5.35, y: 2.35, w: 4.05, h: 2.4, fontSize: 14, fontFace: FONT_BODY, color: C.white, margin: 0, paraSpaceAfter: 6 }
    );
  }

  // 4 GLOSSÁRIO INSTITUIÇÕES
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "GLOSSÁRIO 1 — INSTITUIÇÕES E SISTEMAS");
    addFooter(slide, 4);
    glossTable(slide, [
      ["Sigla", "O que é", "Papel nesta conversa"],
      ["CEDAE", "Companhia Estadual de Águas e Esgotos do RJ", "Produz água; não distribui sozinha após a concessão"],
      ["ETA", "Estação de Tratamento de Água", "A do Guandu é a maior em volume do mundo (~45 m³/s)"],
      ["ANA / SAR", "Agência Nacional de Águas / Sistema de Acompanhamento de Reservatórios", "Cota e volume útil diários (Funil, Paraibuna…)"],
      ["CEIVAP / INEA", "Comitê da bacia do Paraíba do Sul / Instituto Estadual do Ambiente", "Outorga e regras da transposição"],
      ["LIGHT", "Operadora da transposição Paraíba → Guandu", "Quem bombeia em Santa Cecília"],
      ["INMET", "Instituto Nacional de Meteorologia", "SPI de seca e estações oficiais"],
      ["CEMADEN", "Centro Nacional de Monitoramento e Alertas de Desastres", "Alerta técnico à Defesa Civil — não à população"],
      ["COR / GEO-RIO", "Centro de Operações Rio / fundação geotécnica", "Alerta Rio, sirenes, estágios 1–5"],
      ["SOP", "Standard Operating Procedure — procedimento padrão", "O que fazer quando o limiar estoura"],
    ], 0.82, 0.43);
  }

  // 5 GLOSSÁRIO GRANDEZAS
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "GLOSSÁRIO 2 — GRANDEZAS E NOMENCLATURA");
    addFooter(slide, 5);
    glossTable(slide, [
      ["Termo", "O que mede", "Como ler"],
      ["mm / mm/h", "Chuva: milímetros (lâmina) e milímetros por hora (intensidade)", "Alerta Rio: fraca <5, moderada 5–25, forte 25–50, muito forte >50 mm/h"],
      ["m³/s", "Vazão — metros cúbicos por segundo", "ETA Guandu outorgada em 45 m³/s"],
      ["Volume útil (VU)", "Água armazenada entre o mínimo e o máximo operativos", "Equivalente Paraíba: 33% em jan/2026 (ANA)"],
      ["Outorga", "Direito de usar uma vazão, dado pelo órgão ambiental", "Teto legal da captação, não a produção do dia"],
      ["uT (turbidez)", "Unidade de turbidez (equivalente a NTU)", "Portaria 888: 0,5 uT na filtração; 5 uT na rede"],
      ["Manancial", "Corpo d’água de onde se capta", "Guandu = Lajes + transposição do Paraíba do Sul"],
      ["PMSB / PDDU", "Plano municipal de saneamento / plano diretor", "Pedem chuva de 10, 50, 100 anos — período de retorno"],
      ["199", "Telefone da Defesa Civil (Anatel 357/2004)", "Não é o nome de um protocolo; o SOP local é outro"],
      ["A2C2", "Sistema de Alerta e Alarme Comunitário (sirenes)", "Dispara com 40 mm em 1 h ou 125 mm em 24 h"],
    ], 0.82, 0.43);
  }

  // 6 GLOSSÁRIO MATH 1
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "GLOSSÁRIO 3 — MATEMÁTICA DE PREVISÃO E CAUDA");
    addFooter(slide, 6);
    glossTable(slide, [
      ["Nome", "Em uma frase", "Não serve para"],
      ["LSTM", "Rede que lê uma sequência de dias e prevê o próximo valor", "Dimensionar drenagem de 50 anos"],
      ["Atenção", "Peso α_t que diz quais dias do passado importam mais para o ŷ", "Substituir o pluviômetro"],
      ["Bootstrap de resíduos", "Sorteia o erro real do LSTM; gera uma faixa, não um milímetro único", "Inventar série de clima"],
      ["GEV", "Lei dos máximos de bloco (ex.: máximo anual de chuva)", "Prever a chuva de amanhã"],
      ["Período de retorno T", "Chuva que, em média, é igualada ou excedida a cada T anos", "Garantir que não chova esse valor em T anos"],
      ["GPD / POT", "Lei dos picos acima de um limiar u (Peaks Over Threshold)", "Regime de estiagem de meses"],
      ["P10 / P90", "10% e 90% da distribuição simulada — banda de incerteza", "Um único número para o gabinete"],
    ], 0.88, 0.52);
  }

  // 7 GLOSSÁRIO MATH 2
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "GLOSSÁRIO 4 — REGIME, SECA, ESPAÇO E GATILHO");
    addFooter(slide, 7);
    glossTable(slide, [
      ["Nome", "Em uma frase", "Não serve para"],
      ["HMM", "Estados ocultos (úmido / seco / árido) que mudam com o tempo", "Aviso de 6 horas de alagamento"],
      ["ENSO / ONI / RONI", "Oscilação do Pacífico; ONI e RONI são os índices da NOAA", "Operar a ETA na próxima hora"],
      ["SPI", "Chuva padronizada (WMO). SPI-3 = trimestre; SPI-12 = ano hidrológico", "Intensidade de chuva em 15 minutos"],
      ["SPEI", "SPI + evapotranspiração — a seca também aquece", "Substituir o volume útil do Funil"],
      ["KDE", "Densidade espacial suave (onde o risco se concentra no mapa)", "Uma cota de reservatório"],
      ["DBSCAN", "Agrupa pontos próximos sem fixar o número de grupos", "Previsão de vazão"],
      ["R físico = p·λ·v", "Probabilidade × frequência × vulnerabilidade do ativo", "Qualidade da água (uT)"],
      ["Gatilho paramétrico", "Se valor observado ≥ limiar, dispara o SOP", "Calcular o período de retorno"],
      ["Cópula", "Dependência entre extremos de duas bacias ao mesmo tempo", "Um único pluviômetro"],
    ], 0.82, 0.43);
  }

  // 8 FAMÍLIA
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "POR QUE NÃO EXISTE UM ÚNICO MODELO");
    addGoldStripe(slide, pres);
    addFooter(slide, 8);
    slide.addText("Cada pergunta operacional vive numa escala de tempo e num objeto diferente. O motor certo é o que responde aquela pergunta — não o mais sofisticado.", {
      x: 0.5, y: 0.85, w: 9.0, h: 0.55,
      fontSize: 14, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
    });
    const fam = [
      { t: "Horas", q: "Chove acima de 40 mm nesta hora?", m: "LSTM + gatilho", w: "Sequência recente + limiar já usado pelas sirenes" },
      { t: "Dias", q: "A ETA vai perder tratabilidade amanhã?", m: "POT / GPD", w: "O evento é um pico acima do limiar, não a média" },
      { t: "Meses", q: "Entramos em estiagem?", m: "HMM + SPI/SPEI + ENSO", w: "Seca é regime, não um dia isolado" },
      { t: "Anos", q: "Qual chuva de 50 anos para a drenagem?", m: "GEV", w: "Projeto pede período de retorno, não previsão" },
      { t: "Espaço", q: "Qual bairro ou setor de rede?", m: "KDE + DBSCAN", w: "Ação é geográfica; o ponto único mente" },
      { t: "Ativo", q: "A ETA ou a escola quebra?", m: "R = p·λ·v", w: "Mesma chuva, vulnerabilidades diferentes" },
    ];
    fam.forEach((f, i) => {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const x = 0.4 + col * 3.15;
      const y = 1.5 + row * 1.8;
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y, w: 3.0, h: 1.65, fill: { color: C.offWhite },
      });
      slide.addText(f.t, {
        x: x + 0.12, y: y + 0.08, w: 2.76, h: 0.26,
        fontSize: 12, fontFace: FONT_HEADER, color: C.gold, bold: true, margin: 0,
      });
      slide.addText(f.q, {
        x: x + 0.12, y: y + 0.34, w: 2.76, h: 0.4,
        fontSize: 12, fontFace: FONT_HEADER, color: C.navy, bold: true, margin: 0,
      });
      slide.addText(f.m, {
        x: x + 0.12, y: y + 0.76, w: 2.76, h: 0.28,
        fontSize: 12, fontFace: FONT_BODY, color: C.teal, bold: true, margin: 0,
      });
      slide.addText(f.w, {
        x: x + 0.12, y: y + 1.06, w: 2.76, h: 0.48,
        fontSize: 11, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
      });
    });
  }

  // 9 LSTM
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "MÓDULO — LSTM COM ATENÇÃO  +  BOOTSTRAP");
    addGoldStripe(slide, pres);
    addFooter(slide, 9);
    slide.addText("O que é.  LSTM (Long Short-Term Memory) é uma rede recorrente: lê x_t = [temperatura, chuva, pressão, vento, ENSO] dia a dia. A atenção calcula α_t = softmax(vᵀ tanh(W_h h_t + W_c c_t)) e a previsão é ŷ = Σ α_t · h_t — uma média ponderada do passado relevante, não de todos os dias iguais.", {
      x: 0.45, y: 0.82, w: 9.1, h: 1.15,
      fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
    });
    whyBox(slide, pres, 0.4, 2.08, 4.5, 2.95,
      "Situação",
      "Defesa Civil precisa de 6–48 h: vai chover o bastante para alagar? A ETA precisa do mesmo horizonte: a captação de amanhã vem mais suja?\n\nO ClimateWise já treina isso no arquivo Open-Meteo, sem série sintética. O bootstrap sorteia os resíduos reais do ajuste e devolve uma faixa (não um milímetro teatral)."
    );
    whyBox(slide, pres, 5.1, 2.08, 4.5, 2.95,
      "Por que este — e não GEV ou HMM",
      "GEV responde “chuva de 50 anos”: é projeto, não amanhã.\nHMM responde “estamos secos neste trimestre”: é regime, não a próxima hora.\n\nA LSTM é adequada porque a pergunta é de sequência curta com as mesmas variáveis que a estação já mede. A atenção evita tratar um dia de 2019 igual ao de ontem."
    );
  }

  // 10 GEV
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "MÓDULO — GEV, GPD E POT (TEORIA DE VALORES EXTREMOS)");
    addGoldStripe(slide, pres);
    addFooter(slide, 10);
    slide.addText("O que é.  A teoria de valores extremos descreve a cauda, não a média. GEV ajusta máximos de bloco (ex.: o maior dia de cada ano) com parâmetros μ (posição), σ (escala) e ξ (forma). GPD / POT (Peaks Over Threshold) ajusta só o que passa de um limiar u — aproveita mais eventos do que um máximo por ano. O período de retorno T é o nível que, em média, é excedido a cada T anos.", {
      x: 0.45, y: 0.82, w: 9.1, h: 1.2,
      fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
    });
    whyBox(slide, pres, 0.4, 2.12, 4.5, 2.9,
      "Situação",
      "Prefeitura: o PMSB e o PDDU pedem a chuva de 10, 25, 50 e 100 anos para galeria e zona de risco.\n\nCEDAE: a ETA não para pela média do mês; para (ou reduz, como em out/2024 a 73%) quando um pico de chuva a montante piora a água bruta. Isso é POT, não média móvel."
    );
    whyBox(slide, pres, 5.1, 2.12, 4.5, 2.9,
      "Por que este — e não LSTM",
      "LSTM extrapola o dia seguinte; não tem o direito estatístico de falar em “50 anos”.\n\nGEV é o instrumento clássico de engenharia hidráulica para período de retorno. GPD é o mais adequado ao aviso de tratabilidade porque o fenômeno é “passou do limiar”, exatamente a definição de pico sobre limiar."
    );
  }

  // 11 HMM ENSO
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "MÓDULO — HMM DE REGIME  +  ENSO (ONI / RONI)");
    addGoldStripe(slide, pres);
    addFooter(slide, 11);
    slide.addText("O que é.  HMM (Hidden Markov Model) supõe estados que não vemos direto — no ClimateWise: úmido, seco, árido — com transições P(S_t = j | S_{t-1} = i) = A_ij(ΔT). ENSO é a oscilação El Niño / La Niña no Pacífico. ONI e RONI, da NOAA CPC, classificam o regime com persistência de cinco estações sobrepostas (DJF, JFM…).", {
      x: 0.45, y: 0.82, w: 9.1, h: 1.15,
      fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
    });
    whyBox(slide, pres, 0.4, 2.08, 4.5, 2.95,
      "Situação",
      "A CEDAE não raciona por causa de uma tarde sem chuva. Raciona quando o equivalente Paraíba cai (33% em jan/2026) e a transposição da LIGHT aperta.\n\nA prefeitura comunica estiagem em escala de meses. 2014–15 e 2015–17 no RJ foram anos secos no SPEI-12 — regime, não episódio."
    );
    whyBox(slide, pres, 5.1, 2.08, 4.5, 2.95,
      "Por que este — e não LSTM ou GEV",
      "LSTM olha dias; GEV olha caudas anuais. Nenhum dos dois diz “mudamos de estado climático”.\n\nHMM é o instrumento de mudança de regime. ENSO é o forçante sazonal observado (não inventado) que altera a probabilidade de o Sudeste entrar no estado seco. Juntos cobrem 3–9 meses de alocação."
    );
  }

  // 12 ESPAÇO GATILHO
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "MÓDULO — ESPAÇO, ATIVO E GATILHO");
    addFooter(slide, 12);
    const cards = [
      { t: "KDE e DBSCAN", w: "O que. Densidade no mapa e agrupamento de pontos de extremo.\nPor quê. Sirene, bomba e caminhão não atuam “no município”: atuam no bairro. Um único pluviômetro é o objeto errado. DBSCAN acha o cluster sem exigir o número de grupos." },
      { t: "R físico = p · λ · v", w: "O que. p vem do GEV; λ é a taxa anual ajustada; v é fragilidade (idade, material, cota).\nPor quê. A mesma chuva que alaga a via pode parar a ETA (Marapicu, fev/2026) e poupar uma escola em cota alta. Sem v, o mapa mente." },
      { t: "Gatilho paramétrico", w: "O que. Se valor ≥ limiar, dispara. Nasceu para indenização.\nPor quê. O SOP do Rio já é isso: 40 mm/1 h ou 125 mm/24 h nas sirenes A2C2. Reciclar o motor de seguro para o protocolo que a cidade já usa — não inventar uma escala nova." },
    ];
    cards.forEach((c, i) => {
      const x = 0.35 + i * 3.15;
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y: 0.88, w: 3.05, h: 4.2, fill: { color: C.offWhite },
      });
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y: 0.88, w: 3.05, h: 0.08, fill: { color: i === 2 ? C.gold : C.navy },
      });
      slide.addText(c.t, {
        x: x + 0.14, y: 1.08, w: 2.77, h: 0.7,
        fontSize: 15, fontFace: FONT_HEADER, color: C.navy, bold: true, margin: 0,
      });
      slide.addText(c.w, {
        x: x + 0.14, y: 1.82, w: 2.77, h: 3.05,
        fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
      });
    });
  }

  // 13 SPI
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "MÓDULO — SPI, SPEI E O RESERVATÓRIO (O DADO QUE JÁ EXISTE)");
    addGoldStripe(slide, pres);
    addFooter(slide, 13);
    slide.addText("O que é.  SPI (Standardized Precipitation Index) transforma a chuva acumulada em desvios-padrão, comparáveis entre climas. A OMM (WMO) o elegeu como índice meteorológico de seca. SPI-1 = mês; SPI-3 = trimestre agrícola; SPI-12 = ano hidrológico. SPEI acrescenta a evapotranspiração (Penman–Monteith): com o aquecimento, a mesma chuva seca mais.", {
      x: 0.45, y: 0.82, w: 9.1, h: 1.2,
      fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
    });
    whyBox(slide, pres, 0.4, 2.12, 4.5, 2.9,
      "Situação",
      "INMET já publica mapas de SPI. ALARMES/UFRJ publica SPEI. ANA SAR já publica o volume útil de Funil, Paraibuna, Jaguari e Santa Branca.\n\nO ClimateWise ainda não lê esses índices. Não deve criar um “índice ClimateWise de seca”: deve falar a língua oficial."
    );
    whyBox(slide, pres, 5.1, 2.12, 4.5, 2.9,
      "Por que SPI/SPEI + SAR — e não só HMM",
      "HMM detecta mudança de estado nos nossos dados. SPI é o vocabulário que INMET, CEMADEN e comitês de bacia já usam. SAR é a cota real do reservatório — o objeto da CEDAE.\n\nHMM antecipa; SPI comunica; SAR confirma. Os três juntos. Nenhum sozinho fecha o racionamento."
    );
  }

  // 14 NÚMEROS
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "CONTEXTO — GUANDU E PARAÍBA EM NÚMEROS OFICIAIS");
    addFooter(slide, 14);
    const nums = [
      { n: "1,30 bi", u: "m³ em 2025", d: "Guandu = 72% da produção CEDAE no Estado (1,81 bi m³)" },
      { n: "45", u: "m³/s", d: "Outorga da ETA Guandu — cerca de 9 milhões de pessoas" },
      { n: "33%", u: "volume útil", d: "Equivalente Paraíba em jan/2026 (ANA); 65% um ano antes" },
      { n: "73%", u: "da ETA", d: "Out/2024: chuva na bacia piorou a água bruta" },
    ];
    nums.forEach((s, i) => {
      const x = 0.4 + i * 2.4;
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y: 0.88, w: 2.25, h: 1.7,
        fill: { color: i % 2 === 0 ? C.navy : C.offWhite },
        shadow: makeShadow(),
      });
      slide.addText(s.n, {
        x, y: 0.96, w: 2.25, h: 0.48,
        fontSize: 22, fontFace: FONT_HEADER, color: i % 2 === 0 ? C.gold : C.navy,
        bold: true, align: "center", margin: 0,
      });
      slide.addText(s.u, {
        x: x + 0.08, y: 1.44, w: 2.09, h: 0.26,
        fontSize: 12, fontFace: FONT_HEADER, color: i % 2 === 0 ? C.white : C.navy,
        bold: true, align: "center", margin: 0,
      });
      slide.addText(s.d, {
        x: x + 0.1, y: 1.74, w: 2.05, h: 0.72,
        fontSize: 11, fontFace: FONT_BODY, color: i % 2 === 0 ? C.lightGray : C.bodyText,
        align: "center", margin: 0,
      });
    });
    const rows = [
      ["O fato", "O que o modelo deve fazer com ele"],
      ["Transposição LIGHT: Guandu natural 7–25 m³/s → ~150 m³/s", "ENSO + HMM + SAR: a vazão extra não é clima local; é operação"],
      ["Sirenes A2C2: 40 mm/1 h ou 125 mm/24 h", "Gatilho paramétrico = esse limiar, não uma escala nova"],
      ["Portaria 888: 0,5 uT na filtração, 5 uT na rede", "POT de chuva a montante avisa o pico; não substitui o turbidímetro"],
      ["CEMADEN alerta a Defesa Civil, não o cidadão", "O produto alimenta a sala de situação; o 199 e o cell broadcast são do município"],
    ];
    const hOpts = () => ({
      fontSize: 11, fontFace: FONT_BODY, bold: true, color: C.white,
      fill: { color: C.navy }, valign: "middle",
      border: [{ pt: 0.5, color: C.navy }], margin: [3, 6, 3, 6],
    });
    const gCell = (alt, bold) => ({
      fontSize: 11, fontFace: FONT_BODY, color: bold ? C.navy : C.bodyText, bold: !!bold,
      fill: { color: alt ? C.offWhite : C.white }, valign: "middle",
      border: [{ pt: 0.5, color: C.lightGray }], margin: [3, 6, 3, 6],
    });
    slide.addTable(
      rows.map((row, ri) => {
        if (ri === 0) return row.map((c) => ({ text: c, options: hOpts() }));
        const alt = ri % 2 === 0;
        return [
          { text: row[0], options: gCell(alt, true) },
          { text: row[1], options: gCell(alt, false) },
        ];
      }),
      { x: 0.4, y: 2.75, w: 9.2, colW: [4.4, 4.8], rowH: 0.48 }
    );
  }

  // 15 TABELA POR QUE
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "SITUAÇÃO → MÓDULO → POR QUE ESTE");
    addFooter(slide, 15);
    const headerOpts = () => ({
      fontSize: 10, fontFace: FONT_BODY, bold: true, color: C.white,
      fill: { color: C.navy }, valign: "middle",
      border: [{ pt: 0.5, color: C.navy }], margin: [3, 4, 3, 4],
    });
    const cell = (alt, bold) => ({
      fontSize: 10, fontFace: FONT_BODY,
      color: bold ? C.navy : C.bodyText, bold: !!bold,
      fill: { color: alt ? C.offWhite : C.white }, valign: "middle",
      border: [{ pt: 0.5, color: C.lightGray }], margin: [3, 4, 3, 4],
    });
    const rows = [
      ["Situação", "Módulo", "Por que é o adequado"],
      ["Aviso 6–48 h de alagamento", "LSTM + atenção", "Pergunta de sequência curta com as variáveis da estação"],
      ["Não mentir um milímetro só", "Bootstrap de resíduos", "Usa o erro real do modelo; não gera clima falso"],
      ["Galeria / PMSB 10–100 anos", "GEV", "Período de retorno é definição de máximos de bloco"],
      ["Pico que suja a ETA", "GPD / POT", "O fenômeno é exceder o limiar, não o máximo anual"],
      ["Estiagem de meses", "HMM + SPI/SPEI", "Regime + língua oficial do INMET"],
      ["Alocação 3–9 meses", "ENSO ONI/RONI", "Forçante sazonal observado pela NOAA, não um proxy"],
      ["Qual bairro evacuar", "KDE + DBSCAN", "Ação é espacial; o ponto único não localiza o cluster"],
      ["ETA vs. escola na mesma chuva", "R = p·λ·v", "Separa perigo (p) de vulnerabilidade do ativo (v)"],
      ["Sirene / SOP", "Gatilho paramétrico", "Já é o formato A2C2 (40 mm/1 h, 125 mm/24 h)"],
      ["Guandu e cidade no mesmo dia", "Cópula", "Extremos conjuntos; duas bacias não são independentes"],
    ];
    slide.addTable(
      rows.map((row, ri) => {
        if (ri === 0) return row.map((c) => ({ text: c, options: headerOpts() }));
        const alt = ri % 2 === 0;
        return row.map((c, ci) => ({ text: c, options: cell(alt, ci === 0) }));
      }),
      { x: 0.28, y: 0.82, w: 9.44, colW: [2.7, 2.2, 4.54], rowH: 0.4 }
    );
  }

  // 16 MUNICIPAL APPLY
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "NA PREFEITURA — DO LIMIAR OFICIAL AO MOTOR");
    addGoldStripe(slide, pres);
    addFooter(slide, 16);
    const steps = [
      { h: "Alerta Rio mede", d: "33 estações, 15 min. Intensidade oficial: <5 / 5–25 / 25–50 / >50 mm/h. Isso é o dado; o modelo não redefine “chuva forte”." },
      { h: "LSTM estima", d: "A probabilidade de, nas próximas 6–48 h, cruzar 40 mm em 1 h ou 125 mm em 24 h — os limiares das sirenes A2C2." },
      { h: "KDE aponta o bairro", d: "O COR não evacua a cidade inteira. O cluster espacial diz onde tocar a sirene e abrir ponto de apoio." },
      { h: "GEV alimenta o plano", d: "Fora da emergência: período de retorno para drenagem e PDDU. Outra pergunta, outro motor." },
    ];
    steps.forEach((s, i) => {
      const y = 0.88 + i * 1.05;
      slide.addShape(pres.shapes.OVAL, {
        x: 0.5, y: y + 0.18, w: 0.42, h: 0.42, fill: { color: C.navy },
      });
      slide.addText(String(i + 1), {
        x: 0.5, y: y + 0.18, w: 0.42, h: 0.42,
        fontSize: 14, fontFace: FONT_HEADER, color: C.white, bold: true,
        align: "center", valign: "middle", margin: 0,
      });
      slide.addText(s.h, {
        x: 1.1, y: y, w: 8.3, h: 0.32,
        fontSize: 15, fontFace: FONT_HEADER, color: C.navy, bold: true, margin: 0,
      });
      slide.addText(s.d, {
        x: 1.1, y: y + 0.34, w: 8.3, h: 0.58,
        fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
      });
    });
  }

  // 17 CEDAE APPLY
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "NA CEDAE — DO MANANCIAL À ETA, COM O MOTOR CERTO");
    addFooter(slide, 17);
    const items = [
      { icon: iconWater, t: "Manancial (meses)", d: "HMM + ENSO + SPI + SAR. Por quê: a transposição LIGHT e o equivalente Paraíba são regime hidrológico. LSTM de amanhã não decide racionamento." },
      { icon: iconIndustry, t: "ETA (horas–dias)", d: "POT de chuva a montante + LSTM. Por quê: out/2024 a 73% foi pico de qualidade da bruta, não média. O turbidímetro continua soberano; o modelo avisa o pico." },
      { icon: iconRain, t: "Rede (horas)", d: "LSTM urbano + R físico nas elevatórias. Por quê: chuva forte sobrecarrega esgoto no mesmo objeto geográfico do alagamento municipal." },
      { icon: iconChart, t: "Ativo (anos)", d: "GEV + v do ativo. Por quê: a adutora de Marapicu (fev/2026, 50%) não tem a mesma v de um reservatório de bairro. p igual, prejuízo diferente." },
    ];
    items.forEach((it, i) => {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = 0.4 + col * 4.8;
      const y = 0.9 + row * 2.05;
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y, w: 4.6, h: 1.9, fill: { color: C.offWhite },
      });
      slide.addImage({ data: it.icon, x: x + 0.14, y: y + 0.14, w: 0.3, h: 0.3 });
      slide.addText(it.t, {
        x: x + 0.52, y: y + 0.12, w: 3.9, h: 0.34,
        fontSize: 14, fontFace: FONT_HEADER, color: C.navy, bold: true, margin: 0,
      });
      slide.addText(it.d, {
        x: x + 0.14, y: y + 0.52, w: 4.32, h: 1.25,
        fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0,
      });
    });
  }

  // 18 API
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "COMO ISSO CHEGA — PARTNER API E FONTES");
    addFooter(slide, 18);
    const src = [
      { t: "Já no ClimateWise", d: "Open-Meteo (arquivo e forecast), NOAA CPC (ONI/RONI), CEMADEN, INMET. LSTM, GEV, HMM, KDE, gatilho. Envelope {data, meta} com fresh | stale | unavailable." },
      { t: "A acoplar (públicos)", d: "Alerta Rio 15 min · ANA SAR · SIGA-Ceivap · SPI/INMET · SPEI/ALARMES · relatórios Guandu / SISÁGUA (Portaria 888)." },
      { t: "Regra de honra", d: "Se o upstream falha, status unavailable. Não se inventa milímetro, uT nem volume útil para gabinete ou sala de situação." },
      { t: "O que não somos", d: "Não somos SCADA, hidrólogo da LIGHT nem o 199. Alimentamos a decisão com o motor certo para cada pergunta." },
    ];
    src.forEach((s, i) => {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = 0.4 + col * 4.8;
      const y = 0.9 + row * 2.05;
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y, w: 4.6, h: 1.9, fill: { color: row === 1 && col === 1 ? C.navy : C.offWhite },
      });
      slide.addText(s.t, {
        x: x + 0.18, y: y + 0.12, w: 4.24, h: 0.36,
        fontSize: 15, fontFace: FONT_HEADER,
        color: row === 1 && col === 1 ? C.gold : C.navy, bold: true, margin: 0,
      });
      slide.addText(s.d, {
        x: x + 0.18, y: y + 0.52, w: 4.24, h: 1.22,
        fontSize: 13, fontFace: FONT_BODY,
        color: row === 1 && col === 1 ? C.white : C.bodyText, margin: 0,
      });
    });
  }

  // 19 FONTES
  {
    const slide = pres.addSlide();
    slide.background = { color: C.white };
    addHeaderBar(slide, pres, "FONTES PÚBLICAS (AGO/2026)");
    addFooter(slide, 19);
    slide.addText(
      [
        { text: "CEDAE — Relatório anual Guandu 2025: 1,805 bi m³ no Estado; 1,299 bi m³ no Guandu.", options: { bullet: true, breakLine: true } },
        { text: "CEIVAP / INEA — ETA Guandu ~43 m³/s (outorga 45 m³/s); transposição LIGHT.", options: { bullet: true, breakLine: true } },
        { text: "ANA SAR / imprensa jan 2026 — equivalente Paraíba em 33,3% do VU (65,5% em jan/2025).", options: { bullet: true, breakLine: true } },
        { text: "Resolução ANA/IGAM/DAEE/INEA 1.382/2015 — Santa Cecília 250 / 190 m³/s.", options: { bullet: true, breakLine: true } },
        { text: "Portaria GM/MS 888/2021 — turbidez 0,5 uT (filtração) e 5 uT (rede).", options: { bullet: true, breakLine: true } },
        { text: "Alerta Rio / GEO-RIO — classes mm/h; A2C2 40 mm/1 h ou 125 mm/24 h.", options: { bullet: true, breakLine: true } },
        { text: "CEMADEN — alerta à Defesa Civil; CEMADEN-RJ 70 PCDs / 13 municípios.", options: { bullet: true, breakLine: true } },
        { text: "Anatel 357/2004 — telefone 199. SMS municipal: CEP para 40199.", options: { bullet: true, breakLine: true } },
        { text: "INMET (SPI) · ALARMES/UFRJ (SPEI) · WMO — SPI como índice padrão de seca.", options: { bullet: true } },
      ],
      {
        x: 0.5, y: 0.88, w: 9.0, h: 4.25,
        fontSize: 13, fontFace: FONT_BODY, color: C.bodyText, margin: 0, paraSpaceAfter: 5,
      }
    );
  }

  // 20 CLOSE
  {
    const slide = pres.addSlide();
    slide.background = { color: C.navy };
    addGoldStripe(slide, pres);
    slide.addText("EM UMA FRASE", {
      x: 0.55, y: 0.4, w: 9, h: 0.3,
      fontSize: 13, fontFace: FONT_BODY, color: C.gold, bold: true, charSpacing: 2, margin: 0,
    });
    slide.addText("Usar o motor da pergunta certa.\nFalar a língua oficial do dado.", {
      x: 0.55, y: 0.8, w: 9, h: 1.15,
      fontSize: 24, fontFace: FONT_HEADER, color: C.white, bold: true, margin: 0,
    });
    const road = [
      { d: "90 dias", t: "Sala municipal", b: "Gatilho = A2C2 (40 mm/1 h, 125 mm/24 h) + LSTM + cluster KDE. Glossário no painel." },
      { d: "180 dias", t: "Sinal CEDAE", b: "SAR/ANA + SPI/INMET no manancial; POT como aviso de tratabilidade da ETA." },
      { d: "365 dias", t: "Acoplamento", b: "Chuva–vazão com LIGHT/ANA. SPEI calibrado. SOP COR 1–5. A matemática-base permanece." },
    ];
    road.forEach((r, i) => {
      const x = 0.55 + i * 3.05;
      slide.addShape(pres.shapes.RECTANGLE, {
        x, y: 2.15, w: 2.9, h: 2.35, fill: { color: C.navyDark },
      });
      slide.addText(r.d, {
        x: x + 0.15, y: 2.28, w: 2.6, h: 0.28,
        fontSize: 12, fontFace: FONT_BODY, color: C.gold, bold: true, margin: 0,
      });
      slide.addText(r.t, {
        x: x + 0.15, y: 2.58, w: 2.6, h: 0.38,
        fontSize: 16, fontFace: FONT_HEADER, color: C.white, bold: true, margin: 0,
      });
      slide.addText(r.b, {
        x: x + 0.15, y: 3.02, w: 2.6, h: 1.3,
        fontSize: 13, fontFace: FONT_BODY, color: C.lightGray, margin: 0,
      });
    });
    slide.addText("ClimateWise  ·  glossário, motor certo, envelope honesto  ·  agosto 2026", {
      x: 0.55, y: 4.7, w: 9, h: 0.32,
      fontSize: 12, fontFace: FONT_BODY, color: C.midGray, margin: 0,
    });
  }

  const out = "/Users/leandrofrancademello/Projetos/ClimateWise/docs/ClimateWise-Municipal-CEDAE.pptx";
  const desktop = "/Users/leandrofrancademello/Desktop/ClimateWise-Municipal-CEDAE.pptx";
  await pres.writeFile({ fileName: out });
  await pres.writeFile({ fileName: desktop });
  console.log("WROTE", out);
  console.log("WROTE", desktop);
}

buildPresentation().catch((err) => {
  console.error(err);
  process.exit(1);
});

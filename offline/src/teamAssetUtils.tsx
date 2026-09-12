import React, { useState } from 'react';
import { getFlag } from './flagUtils';

// ── Known Canonical Club Crests ───────────────────────────────────────────────
// Stable, high-resolution club crest URLs (football-data.org CDN / official Wikimedia / TheSportsDB)
export const CANONICAL_CLUB_CRESTS: Record<string, string> = {
  // English Premier League
  'arsenal': 'https://crests.football-data.org/57.png',
  'arsenal fc': 'https://crests.football-data.org/57.png',
  'aston villa': 'https://crests.football-data.org/58.png',
  'aston villa fc': 'https://crests.football-data.org/58.png',
  'chelsea': 'https://crests.football-data.org/61.png',
  'chelsea fc': 'https://crests.football-data.org/61.png',
  'everton': 'https://crests.football-data.org/62.png',
  'everton fc': 'https://crests.football-data.org/62.png',
  'fulham': 'https://crests.football-data.org/63.png',
  'fulham fc': 'https://crests.football-data.org/63.png',
  'liverpool': 'https://crests.football-data.org/64.png',
  'liverpool fc': 'https://crests.football-data.org/64.png',
  'manchester city': 'https://crests.football-data.org/65.png',
  'manchester city fc': 'https://crests.football-data.org/65.png',
  'manchester united': 'https://crests.football-data.org/66.png',
  'manchester united fc': 'https://crests.football-data.org/66.png',
  'newcastle united': 'https://crests.football-data.org/67.png',
  'newcastle united fc': 'https://crests.football-data.org/67.png',
  'tottenham hotspur': 'https://crests.football-data.org/73.png',
  'tottenham hotspur fc': 'https://crests.football-data.org/73.png',
  'tottenham': 'https://crests.football-data.org/73.png',
  'spurs': 'https://crests.football-data.org/73.png',
  'wolverhampton wanderers': 'https://crests.football-data.org/76.png',
  'wolverhampton wanderers fc': 'https://crests.football-data.org/76.png',
  'wolves': 'https://crests.football-data.org/76.png',
  'brighton & hove albion': 'https://crests.football-data.org/397.png',
  'brighton & hove albion fc': 'https://crests.football-data.org/397.png',
  'brighton and hove albion': 'https://crests.football-data.org/397.png',
  'brighton': 'https://crests.football-data.org/397.png',
  'brentford': 'https://crests.football-data.org/402.png',
  'brentford fc': 'https://crests.football-data.org/402.png',
  'west ham united': 'https://crests.football-data.org/563.png',
  'west ham united fc': 'https://crests.football-data.org/563.png',
  'west ham': 'https://crests.football-data.org/563.png',
  'crystal palace': 'https://crests.football-data.org/354.png',
  'crystal palace fc': 'https://crests.football-data.org/354.png',
  'nottingham forest': 'https://crests.football-data.org/351.png',
  'nottingham forest fc': 'https://crests.football-data.org/351.png',
  'afc bournemouth': 'https://crests.football-data.org/1044.png',
  'bournemouth': 'https://crests.football-data.org/1044.png',
  'leicester city': 'https://crests.football-data.org/338.png',
  'leicester city fc': 'https://crests.football-data.org/338.png',
  'ipswich town': 'https://crests.football-data.org/349.png',
  'ipswich town fc': 'https://crests.football-data.org/349.png',
  'southampton': 'https://crests.football-data.org/340.png',
  'southampton fc': 'https://crests.football-data.org/340.png',

  // Spanish La Liga
  'real madrid': 'https://crests.football-data.org/86.png',
  'real madrid cf': 'https://crests.football-data.org/86.png',
  'fc barcelona': 'https://crests.football-data.org/81.png',
  'barcelona': 'https://crests.football-data.org/81.png',
  'atletico madrid': 'https://crests.football-data.org/78.png',
  'atletico de madrid': 'https://crests.football-data.org/78.png',
  'club atletico de madrid': 'https://crests.football-data.org/78.png',
  'athletic club': 'https://crests.football-data.org/77.png',
  'athletic bilbao': 'https://crests.football-data.org/77.png',
  'athletic club de bilbao': 'https://crests.football-data.org/77.png',
  'real sociedad': 'https://crests.football-data.org/92.png',
  'real sociedad de futbol': 'https://crests.football-data.org/92.png',
  'villarreal cf': 'https://crests.football-data.org/94.png',
  'villarreal': 'https://crests.football-data.org/94.png',
  'real betis': 'https://crests.football-data.org/90.png',
  'real betis balompie': 'https://crests.football-data.org/90.png',
  'sevilla fc': 'https://crests.football-data.org/559.png',
  'sevilla': 'https://crests.football-data.org/559.png',
  'valencia cf': 'https://crests.football-data.org/95.png',
  'valencia': 'https://crests.football-data.org/95.png',
  'rc celta de vigo': 'https://crests.football-data.org/558.png',
  'celta de vigo': 'https://crests.football-data.org/558.png',
  'celta vigo': 'https://crests.football-data.org/558.png',
  'girona fc': 'https://crests.football-data.org/298.png',
  'girona': 'https://crests.football-data.org/298.png',
  'ca osasuna': 'https://crests.football-data.org/79.png',
  'osasuna': 'https://crests.football-data.org/79.png',
  'rcd mallorca': 'https://crests.football-data.org/89.png',
  'mallorca': 'https://crests.football-data.org/89.png',
  'rcd espanyol': 'https://crests.football-data.org/80.png',
  'espanyol': 'https://crests.football-data.org/80.png',
  'rayo vallecano': 'https://crests.football-data.org/87.png',
  'rayo vallecano de madrid': 'https://crests.football-data.org/87.png',
  'getafe cf': 'https://crests.football-data.org/82.png',
  'getafe': 'https://crests.football-data.org/82.png',
  'ud las palmas': 'https://crests.football-data.org/275.png',
  'las palmas': 'https://crests.football-data.org/275.png',
  'deportivo alaves': 'https://crests.football-data.org/263.png',
  'alaves': 'https://crests.football-data.org/263.png',
  'rc deportivo la coruna': 'https://crests.football-data.org/560.png',
  'deportivo la coruna': 'https://crests.football-data.org/560.png',
  'elche cf': 'https://crests.football-data.org/285.png',

  // Italian Serie A
  'fc internazionale milano': 'https://crests.football-data.org/108.png',
  'inter milan': 'https://crests.football-data.org/108.png',
  'inter': 'https://crests.football-data.org/108.png',
  'ac milan': 'https://crests.football-data.org/98.png',
  'milan': 'https://crests.football-data.org/98.png',
  'juventus fc': 'https://crests.football-data.org/109.png',
  'juventus': 'https://crests.football-data.org/109.png',
  'as roma': 'https://crests.football-data.org/100.png',
  'roma': 'https://crests.football-data.org/100.png',
  'ssc napoli': 'https://crests.football-data.org/113.png',
  'napoli': 'https://crests.football-data.org/113.png',
  'atalanta bc': 'https://crests.football-data.org/102.png',
  'atalanta': 'https://crests.football-data.org/102.png',
  'ss lazio': 'https://crests.football-data.org/110.png',
  'lazio': 'https://crests.football-data.org/110.png',
  'acf fiorentina': 'https://crests.football-data.org/99.png',
  'fiorentina': 'https://crests.football-data.org/99.png',
  'bologna fc 1909': 'https://crests.football-data.org/103.png',
  'bologna': 'https://crests.football-data.org/103.png',
  'torino fc': 'https://crests.football-data.org/586.png',
  'torino': 'https://crests.football-data.org/586.png',
  'udinese calcio': 'https://crests.football-data.org/115.png',
  'udinese': 'https://crests.football-data.org/115.png',
  'genoa cfc': 'https://crests.football-data.org/107.png',
  'genoa': 'https://crests.football-data.org/107.png',
  'ac monza': 'https://crests.football-data.org/5911.png',
  'monza': 'https://crests.football-data.org/5911.png',
  'hellas verona fc': 'https://crests.football-data.org/450.png',
  'hellas verona': 'https://crests.football-data.org/450.png',
  'cagliari calcio': 'https://crests.football-data.org/104.png',
  'cagliari': 'https://crests.football-data.org/104.png',
  'empoli fc': 'https://crests.football-data.org/445.png',
  'empoli': 'https://crests.football-data.org/445.png',
  'us lecce': 'https://crests.football-data.org/5890.png',
  'lecce': 'https://crests.football-data.org/5890.png',
  'como 1907': 'https://crests.football-data.org/5932.png',
  'como': 'https://crests.football-data.org/5932.png',
  'venezia fc': 'https://crests.football-data.org/454.png',
  'parma calcio 1913': 'https://crests.football-data.org/112.png',

  // German Bundesliga
  'fc bayern munchen': 'https://crests.football-data.org/5.png',
  'fc bayern münchen': 'https://crests.football-data.org/5.png',
  'fc bayern munich': 'https://crests.football-data.org/5.png',
  'bayern munich': 'https://crests.football-data.org/5.png',
  'borussia dortmund': 'https://crests.football-data.org/4.png',
  'dortmund': 'https://crests.football-data.org/4.png',
  'bayer 04 leverkusen': 'https://crests.football-data.org/3.png',
  'bayer leverkusen': 'https://crests.football-data.org/3.png',
  'leverkusen': 'https://crests.football-data.org/3.png',
  'rb leipzig': 'https://crests.football-data.org/721.png',
  'leipzig': 'https://crests.football-data.org/721.png',
  'eintracht frankfurt': 'https://crests.football-data.org/19.png',
  'frankfurt': 'https://crests.football-data.org/19.png',
  'vfb stuttgart': 'https://crests.football-data.org/10.png',
  'stuttgart': 'https://crests.football-data.org/10.png',
  'vfl wolfsburg': 'https://crests.football-data.org/11.png',
  'wolfsburg': 'https://crests.football-data.org/11.png',
  'sc freiburg': 'https://crests.football-data.org/17.png',
  'freiburg': 'https://crests.football-data.org/17.png',
  'borussia monchengladbach': 'https://crests.football-data.org/18.png',
  'borussia mönchengladbach': 'https://crests.football-data.org/18.png',
  'tsg 1899 hoffenheim': 'https://crests.football-data.org/2.png',
  'hoffenheim': 'https://crests.football-data.org/2.png',
  '1. fc union berlin': 'https://crests.football-data.org/28.png',
  'union berlin': 'https://crests.football-data.org/28.png',
  'sv werder bremen': 'https://crests.football-data.org/12.png',
  'werder bremen': 'https://crests.football-data.org/12.png',
  '1. fsv mainz 05': 'https://crests.football-data.org/15.png',
  'mainz': 'https://crests.football-data.org/15.png',
  'fc augsburg': 'https://crests.football-data.org/16.png',
  'augsburg': 'https://crests.football-data.org/16.png',
  '1. fc heidenheim 1846': 'https://crests.football-data.org/44.png',
  '1. fc heidenheim': 'https://crests.football-data.org/44.png',
  'fc heidenheim': 'https://crests.football-data.org/44.png',
  'fc st. pauli 1910': 'https://crests.football-data.org/36.png',
  'holstein kiel': 'https://crests.football-data.org/720.png',
  'vfl bochum 1848': 'https://crests.football-data.org/37.png',

  // French Ligue 1
  'paris saint germain': 'https://crests.football-data.org/524.png',
  'paris saint-germain': 'https://crests.football-data.org/524.png',
  'paris saint-germain fc': 'https://crests.football-data.org/524.png',
  'psg': 'https://crests.football-data.org/524.png',
  'olympique de marseille': 'https://crests.football-data.org/516.png',
  'marseille': 'https://crests.football-data.org/516.png',
  'as monaco fc': 'https://crests.football-data.org/548.png',
  'as monaco': 'https://crests.football-data.org/548.png',
  'monaco': 'https://crests.football-data.org/548.png',
  'olympique lyonnais': 'https://crests.football-data.org/523.png',
  'lyon': 'https://crests.football-data.org/523.png',
  'losc lille': 'https://crests.football-data.org/521.png',
  'lille': 'https://crests.football-data.org/521.png',
  'ogc nice': 'https://crests.football-data.org/522.png',
  'nice': 'https://crests.football-data.org/522.png',
  'stade rennais fc 1901': 'https://crests.football-data.org/529.png',
  'stade rennais fc': 'https://crests.football-data.org/529.png',
  'rennes': 'https://crests.football-data.org/529.png',
  'rc lens': 'https://crests.football-data.org/546.png',
  'lens': 'https://crests.football-data.org/546.png',
  'stade brestois 29': 'https://crests.football-data.org/512.png',
  'brest': 'https://crests.football-data.org/512.png',
  'stade de reims': 'https://crests.football-data.org/547.png',
  'reims': 'https://crests.football-data.org/547.png',
  'rc strasbourg alsace': 'https://crests.football-data.org/576.png',
  'strasbourg': 'https://crests.football-data.org/576.png',
  'toulouse fc': 'https://crests.football-data.org/511.png',
  'montpellier hsc': 'https://crests.football-data.org/518.png',
  'fc nantes': 'https://crests.football-data.org/543.png',

  // Dutch Eredivisie
  'afc ajax': 'https://crests.football-data.org/678.png',
  'ajax': 'https://crests.football-data.org/678.png',
  'psv': 'https://crests.football-data.org/674.png',
  'psv eindhoven': 'https://crests.football-data.org/674.png',
  'feyenoord rotterdam': 'https://crests.football-data.org/675.png',
  'feyenoord': 'https://crests.football-data.org/675.png',
  'az': 'https://crests.football-data.org/682.png',
  'az alkmaar': 'https://crests.football-data.org/682.png',
  'fc twente': 'https://crests.football-data.org/666.png',
  'fc utrecht': 'https://crests.football-data.org/676.png',
  'fortuna sittard': 'https://crests.football-data.org/683.png',

  // Major League Soccer (MLS) — TheSportsDB R2 CDN (verified HTTP 200, image/png)
  'inter miami': 'https://r2.thesportsdb.com/images/media/team/badge/m4it3e1602103647.png',
  'inter miami cf': 'https://r2.thesportsdb.com/images/media/team/badge/m4it3e1602103647.png',
  'fc cincinnati': 'https://r2.thesportsdb.com/images/media/team/badge/vvhsqc1707631046.png',
  'cincinnati': 'https://r2.thesportsdb.com/images/media/team/badge/vvhsqc1707631046.png',
  'columbus crew': 'https://r2.thesportsdb.com/images/media/team/badge/dzs8cp1629059854.png',
  'los angeles fc': 'https://r2.thesportsdb.com/images/media/team/badge/7nbj2a1602103638.png',
  'lafc': 'https://r2.thesportsdb.com/images/media/team/badge/7nbj2a1602103638.png',
  'la galaxy': 'https://r2.thesportsdb.com/images/media/team/badge/ysyysr1420227188.png',
  'los angeles galaxy': 'https://r2.thesportsdb.com/images/media/team/badge/ysyysr1420227188.png',
  'new york red bulls': 'https://r2.thesportsdb.com/images/media/team/badge/suytvy1473536462.png',
  'ny red bulls': 'https://r2.thesportsdb.com/images/media/team/badge/suytvy1473536462.png',
  'new york city fc': 'https://r2.thesportsdb.com/images/media/team/badge/m9vis71735140655.png',
  'nycfc': 'https://r2.thesportsdb.com/images/media/team/badge/m9vis71735140655.png',
  'philadelphia union': 'https://r2.thesportsdb.com/images/media/team/badge/gyznyo1602103682.png',
  'atlanta united': 'https://r2.thesportsdb.com/images/media/team/badge/ej091x1602103070.png',
  'atlanta united fc': 'https://r2.thesportsdb.com/images/media/team/badge/ej091x1602103070.png',
  'seattle sounders': 'https://r2.thesportsdb.com/images/media/team/badge/7em1q51580480820.png',
  'seattle sounders fc': 'https://r2.thesportsdb.com/images/media/team/badge/7em1q51580480820.png',
  'portland timbers': 'https://r2.thesportsdb.com/images/media/team/badge/skm30j1557953559.png',
  'nashville sc': 'https://r2.thesportsdb.com/images/media/team/badge/znrwt71602103062.png',
  'orlando city': 'https://r2.thesportsdb.com/images/media/team/badge/qyppxw1423832326.png',
  'orlando city sc': 'https://r2.thesportsdb.com/images/media/team/badge/qyppxw1423832326.png',
  'toronto fc': 'https://r2.thesportsdb.com/images/media/team/badge/rsxyrr1473536512.png',
  'austin fc': 'https://r2.thesportsdb.com/images/media/team/badge/a3dlg61595434277.png',

  // UEFA Champions League & European Giants
  'sl benfica': 'https://crests.football-data.org/1903.png',
  'benfica': 'https://crests.football-data.org/1903.png',
  'sporting cp': 'https://crests.football-data.org/498.png',
  'sporting': 'https://crests.football-data.org/498.png',
  'fc porto': 'https://crests.football-data.org/503.png',
  'porto': 'https://crests.football-data.org/503.png',
  'celtic fc': 'https://crests.football-data.org/732.png',
  'celtic': 'https://crests.football-data.org/732.png',
  'rangers fc': 'https://crests.football-data.org/731.png',
  'rangers': 'https://crests.football-data.org/731.png',
  'galatasaray sk': 'https://crests.football-data.org/610.png',
  'galatasaray': 'https://crests.football-data.org/610.png',
  'fenerbahce sk': 'https://crests.football-data.org/600.png',
  'fenerbahce': 'https://crests.football-data.org/600.png',
  'fenerbahçe': 'https://crests.football-data.org/600.png',
  'shakhtar donetsk': 'https://crests.football-data.org/620.png',
  'sk slavia praha': 'https://crests.football-data.org/746.png',
  'slavia prague': 'https://crests.football-data.org/746.png',
  'ac sparta praha': 'https://crests.football-data.org/747.png',
  'sparta prague': 'https://crests.football-data.org/747.png',
  'gnk dinamo zagreb': 'https://crests.football-data.org/750.png',
  'dinamo zagreb': 'https://crests.football-data.org/750.png',
  'fk crvena zvezda': 'https://crests.football-data.org/7283.png',
  'red star belgrade': 'https://crests.football-data.org/7283.png',
  'bsc young boys': 'https://crests.football-data.org/1877.png',
  'young boys': 'https://crests.football-data.org/1877.png',
  'fc salzburg': 'https://crests.football-data.org/1871.png',
  'red bull salzburg': 'https://crests.football-data.org/1871.png',
  'club brugge kv': 'https://crests.football-data.org/851.png',
  'club brugge': 'https://crests.football-data.org/851.png',
  'rsc anderlecht': 'https://crests.football-data.org/853.png',
  'royale union saint-gilloise': 'https://crests.football-data.org/453.png',
  'union sg': 'https://crests.football-data.org/453.png',
  'fk bodo/glimt': 'https://crests.football-data.org/5450.png',
  'bodo/glimt': 'https://crests.football-data.org/5450.png',

  // Brazilian Serie A (Brasileirão)
  'cr flamengo': 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Flamengo_braz_logo.svg',
  'flamengo': 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Flamengo_braz_logo.svg',
  'se palmeiras': 'https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg',
  'palmeiras': 'https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg',
  'sao paulo fc': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Brasao_do_Sao_Paulo_Futebol_Clube.svg',
  'sao paulo': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Brasao_do_Sao_Paulo_Futebol_Clube.svg',
  'sc corinthians paulista': 'https://upload.wikimedia.org/wikipedia/en/5/5a/Sport_Club_Corinthians_Paulista_crest.svg',
  'corinthians': 'https://upload.wikimedia.org/wikipedia/en/5/5a/Sport_Club_Corinthians_Paulista_crest.svg',
  'fluminense fc': 'https://upload.wikimedia.org/wikipedia/en/9/9e/Fluminense_FC_crest.svg',
  'fluminense': 'https://upload.wikimedia.org/wikipedia/en/9/9e/Fluminense_FC_crest.svg',
  'gremio fbpa': 'https://upload.wikimedia.org/wikipedia/en/f/f1/Gremio.svg',
  'gremio': 'https://upload.wikimedia.org/wikipedia/en/f/f1/Gremio.svg',
  'sc internacional': 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Escudo_do_Sport_Club_Internacional.svg',
  'internacional': 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Escudo_do_Sport_Club_Internacional.svg',
  'clube atletico mineiro': 'https://upload.wikimedia.org/wikipedia/en/5/5f/Clube_Atl%C3%A9tico_Mineiro_logo.svg',
  'atletico mineiro': 'https://upload.wikimedia.org/wikipedia/en/5/5f/Clube_Atl%C3%A9tico_Mineiro_logo.svg',
  'botafogo fr': 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Escudo_Botafogo.svg',
  'botafogo': 'https://upload.wikimedia.org/wikipedia/commons/c/cb/Escudo_Botafogo.svg',
  'cruzeiro ec': 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Cruzeiro_Esporte_Clube_%28logo%29.svg',
  'cruzeiro': 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Cruzeiro_Esporte_Clube_%28logo%29.svg',
  'cr vasco da gama': 'https://upload.wikimedia.org/wikipedia/en/a/ac/CRVascodaGama.svg',
  'vasco da gama': 'https://upload.wikimedia.org/wikipedia/en/a/ac/CRVascodaGama.svg',
  'santos fc': 'https://upload.wikimedia.org/wikipedia/commons/1/15/Santos_Logo.png',
  'santos': 'https://upload.wikimedia.org/wikipedia/commons/1/15/Santos_Logo.png',
};

// ── Known National Teams List ────────────────────────────────────────────────
// Case-insensitive list of national teams to render country flag emojis
export const NATIONAL_TEAMS = new Set([
  'argentina', 'australia', 'belgium', 'brazil', 'cameroon', 'canada', 'chile',
  'colombia', 'costa rica', 'croatia', 'czech republic', 'czechia', 'denmark',
  'ecuador', 'egypt', 'england', 'france', 'germany', 'ghana', 'greece', 'hungary',
  'iceland', 'iran', 'italy', 'ivory coast', 'japan', 'mexico', 'morocco', 'netherlands',
  'new zealand', 'nigeria', 'norway', 'panama', 'paraguay', 'peru', 'poland', 'portugal',
  'qatar', 'republic of ireland', 'ireland', 'romania', 'saudi arabia', 'scotland', 'senegal',
  'serbia', 'slovakia', 'slovenia', 'south africa', 'south korea', 'korea republic',
  'spain', 'sweden', 'switzerland', 'tunisia', 'turkey', 'türkiye', 'ukraine',
  'united states', 'usa', 'us', 'uruguay', 'wales', 'albania', 'algeria', 'austria',
  'bolivia', 'bosnia and herzegovina', 'bulgaria', 'china', 'dr congo', 'finland',
  'georgia', 'honduras', 'iraq', 'israel', 'jamaica', 'jordan', 'mali', 'montenegro',
  'north macedonia', 'northern ireland', 'oman', 'russia', 'uae', 'united arab emirates',
  'uzbekistan', 'venezuela'
]);

/**
 * Normalise team name for dictionary matching
 */
export function normaliseTeamKey(name: string): string {
  if (!name) return '';
  return name.trim().toLowerCase().replace(/['`]/g, '');
}

/**
 * Check if a team is a recognized national team
 */
export function isNationalTeam(teamName: string): boolean {
  if (!teamName) return false;
  const key = normaliseTeamKey(teamName);
  return NATIONAL_TEAMS.has(key);
}

/**
 * Resolve the visual asset for any team.
 * Returns either an image URL (for club crest) or a flag emoji (for national team).
 */
export function getTeamAsset(teamName: string, passedCrestUrl?: string | null): {
  type: 'image' | 'flag' | 'monogram';
  value: string;
} {
  if (!teamName) return { type: 'flag', value: '🏳️' };

  // 1. National Team check -> Prefer country flag
  if (isNationalTeam(teamName)) {
    const flag = getFlag(teamName);
    if (flag && flag !== '🏳️') {
      return { type: 'flag', value: flag };
    }
  }

  // 2. Passed crest URL from backend/provider
  if (passedCrestUrl && passedCrestUrl.trim().length > 0 && passedCrestUrl.startsWith('http')) {
    return { type: 'image', value: passedCrestUrl };
  }

  // 3. Known canonical club crest lookup
  const key = normaliseTeamKey(teamName);
  if (CANONICAL_CLUB_CRESTS[key]) {
    return { type: 'image', value: CANONICAL_CLUB_CRESTS[key] };
  }

  // Try substring/fuzzy match on known club crests
  for (const [clubKey, url] of Object.entries(CANONICAL_CLUB_CRESTS)) {
    if (key.includes(clubKey) || clubKey.includes(key)) {
      return { type: 'image', value: url };
    }
  }

  // 4. Try national flag as fallback only if getFlag returns a real flag
  const flag = getFlag(teamName);
  if (flag && flag !== '🏳️') {
    return { type: 'flag', value: flag };
  }

  // 5. Monogram fallback (e.g. "ARS", "MIA")
  const initials = teamName
    .split(/\s+/)
    .map(w => w[0])
    .filter(Boolean)
    .slice(0, 3)
    .join('')
    .toUpperCase();

  return { type: 'monogram', value: initials || teamName.substring(0, 3).toUpperCase() };
}

interface TeamBadgeProps {
  name: string;
  crestUrl?: string | null;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

/**
 * TeamBadge Component
 * Gracefully renders club crest images or national flag emojis with zero broken image risk.
 */
export const TeamBadge: React.FC<TeamBadgeProps> = ({
  name,
  crestUrl,
  className = '',
  size = 'md',
}) => {
  const [imgFailed, setImgFailed] = useState(false);
  const asset = getTeamAsset(name, crestUrl);

  const sizeStyles = {
    sm: 'w-4 h-4 text-xs',
    md: 'w-5 h-5 text-sm',
    lg: 'w-7 h-7 text-lg',
    xl: 'w-9 h-9 text-2xl',
  };

  const imgSizeStyles = {
    sm: 'w-4 h-4 max-w-[16px] max-h-[16px]',
    md: 'w-5 h-5 max-w-[20px] max-h-[20px]',
    lg: 'w-7 h-7 max-w-[28px] max-h-[28px]',
    xl: 'w-9 h-9 max-w-[36px] max-h-[36px]',
  };

  if (asset.type === 'image' && !imgFailed) {
    return (
      <span className={`inline-flex items-center justify-center shrink-0 ${sizeStyles[size]} ${className}`}>
        <img
          src={asset.value}
          alt={`${name} crest`}
          className={`${imgSizeStyles[size]} object-contain`}
          loading="lazy"
          onError={() => setImgFailed(true)}
        />
      </span>
    );
  }

  if (asset.type === 'flag' || imgFailed) {
    const flagEmoji = isNationalTeam(name) ? getFlag(name) : null;
    if (flagEmoji && flagEmoji !== '🏳️') {
      return (
        <span className={`inline-flex items-center justify-center select-none shrink-0 leading-none ${sizeStyles[size]} ${className}`}>
          {flagEmoji}
        </span>
      );
    }
  }

  // Monogram / Initials fallback
  const initials = (name || '???')
    .split(/\s+/)
    .map(w => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <span
      className={`inline-flex items-center justify-center shrink-0 rounded bg-zinc-800/80 text-zinc-300 font-mono font-bold text-[9px] border border-zinc-700/50 select-none ${sizeStyles[size]} ${className}`}
      title={name}
    >
      {initials}
    </span>
  );
};

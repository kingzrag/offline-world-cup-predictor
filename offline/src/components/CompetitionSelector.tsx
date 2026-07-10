import { useState, useEffect } from 'react';
import { motion } from 'motion/react';

const competitions = [
  { name: 'FIFA World Cup', logo: '/leagues/world-cup.svg', alt: 'FIFA World Cup' },
  { name: 'Premier League', logo: '/leagues/premier-league.svg', alt: 'Premier League' },
  { name: 'La Liga', logo: '/leagues/la-liga-seeklogo.png', alt: 'La Liga' },
  { name: 'Bundesliga', logo: '/leagues/bundesliga.png', alt: 'Bundesliga' },
  { name: 'Champions League', logo: '/leagues/champions-league.svg', alt: 'Champions League' },
  { name: 'Europa League', logo: '/leagues/europa-league.svg', alt: 'Europa League' },
  { name: 'Serie A', logo: '/leagues/serie-a.svg', alt: 'Serie A' },
];

interface CompetitionSelectorProps {
  isFloating?: boolean;
}

export default function CompetitionSelector({ isFloating = false }: CompetitionSelectorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={`
        bg-[rgba(12,12,12,0.16)] backdrop-blur-md border border-[rgba(255,255,255,0.06)] 
        rounded-[20px] shadow-lg overflow-hidden transition-all duration-500
        ${isFloating 
          ? 'backdrop-blur-lg border-white/10 shadow-2xl' 
          : ''
        }
      `}
      style={{
        boxShadow: isFloating ? '0 0 150px rgba(76,138,131,0.15)' : undefined,
        transition: 'backdrop-filter 0.5s ease, border-color 0.5s ease, box-shadow 0.5s ease'
      }}
    >
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-7 divide-x divide-white/6">
        {competitions.map((comp, index) => (
          <motion.div
            key={comp.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.05, duration: 0.5 }}
            className="relative group px-4 py-3 flex flex-col items-center justify-center cursor-pointer hover:bg-white/3 transition-all duration-250"
            whileHover={{ y: -2 }}
          >
            <img 
              src={comp.logo} 
              alt={comp.alt} 
              className={`object-contain group-hover:scale-[1.08] transition-transform duration-250 ${isFloating ? 'w-8 h-8' : 'w-10 h-10'}`}
              loading="lazy"
              onError={(e) => console.error(`Failed to load logo: ${comp.logo}`, e)}
            />
            <span className={`font-medium text-white uppercase tracking-wide ${isFloating ? 'text-[9px]' : 'text-[11px]'}`}>
              {comp.name}
            </span>
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#22C55E] transform scale-x-0 group-hover:scale-x-100 transition-transform duration-250 origin-center opacity-0 group-hover:opacity-100" />
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

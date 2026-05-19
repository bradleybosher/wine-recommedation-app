import type { CSSProperties } from 'react';
import { INK, INK_SOFT, OXBLOOD, PAPER, RULE, space, typeScale } from '@/design/tokens';

export const ghostBtn: CSSProperties = {
  fontFamily: "'Cormorant Garamond', serif",
  fontSize: typeScale.label,
  letterSpacing: 2,
  textTransform: 'uppercase',
  padding: `${space.xs} ${space.sm}`,
  background: 'transparent',
  color: INK,
  border: `1px solid ${INK}`,
  cursor: 'pointer',
};

export const primaryBtn: CSSProperties = {
  ...ghostBtn,
  background: INK,
  color: PAPER,
};

export const dangerBtn: CSSProperties = {
  ...ghostBtn,
  color: OXBLOOD,
  borderColor: OXBLOOD,
};

export const inputStyle: CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: typeScale.body,
  color: INK,
  background: 'transparent',
  border: `1px solid ${RULE}`,
  padding: `${space.xs} ${space.sm}`,
  width: '100%',
  outline: 'none',
};

export const labelStyle: CSSProperties = {
  display: 'block',
  fontFamily: "'Cormorant Garamond', serif",
  fontStyle: 'italic',
  fontSize: typeScale.micro,
  letterSpacing: 3,
  textTransform: 'uppercase',
  color: OXBLOOD,
  marginBottom: space.xs,
};

export const errorStyle: CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontSize: typeScale.label,
  color: OXBLOOD,
  marginTop: space.xs,
};

export const helperStyle: CSSProperties = {
  fontFamily: "'EB Garamond', serif",
  fontStyle: 'italic',
  fontSize: typeScale.label,
  color: INK_SOFT,
  marginTop: space.xs,
};

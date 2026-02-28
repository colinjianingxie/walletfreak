import { Platform } from 'react-native';

export const shadows = {
  level0: Platform.select({
    ios: {},
    android: { elevation: 0 },
    default: {},
  }),
  level1: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.15,
      shadowRadius: 3,
    },
    android: { elevation: 1 },
    default: {},
  }),
  level2: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 6,
    },
    android: { elevation: 3 },
    default: {},
  }),
  level3: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.15,
      shadowRadius: 8,
    },
    android: { elevation: 6 },
    default: {},
  }),
  level4: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 6 },
      shadowOpacity: 0.15,
      shadowRadius: 12,
    },
    android: { elevation: 8 },
    default: {},
  }),
  level5: Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.18,
      shadowRadius: 16,
    },
    android: { elevation: 12 },
    default: {},
  }),
} as const;

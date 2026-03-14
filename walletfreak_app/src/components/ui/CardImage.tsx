import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Image } from 'expo-image';
import { useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { getCardImage } from '../../utils/images';

const CARD_ASPECT_RATIO = 1.586;

const SIZES: Record<string, { width: number | string; height?: number; aspectRatio?: number }> = {
  tiny: { width: 32, height: 32 / CARD_ASPECT_RATIO },
  small: { width: 48, height: 48 / CARD_ASPECT_RATIO },
  medium: { width: 80, height: 80 / CARD_ASPECT_RATIO },
  large: { width: '100%', aspectRatio: CARD_ASPECT_RATIO },
};

interface CardImageProps {
  slug: string;
  size?: 'tiny' | 'small' | 'medium' | 'large';
  style?: any;
}

export const CardImage: React.FC<CardImageProps> = ({ slug, size = 'medium', style }) => {
  const theme = useTheme();
  const source = getCardImage(slug);
  const dimensions = SIZES[size];

  if (!source) {
    return (
      <View
        style={[
          styles.placeholder,
          {
            width: size === 'large' ? '100%' : dimensions.width,
            height: size === 'large' ? undefined : dimensions.height,
            aspectRatio: size === 'large' ? CARD_ASPECT_RATIO : undefined,
            backgroundColor: theme.colors.surfaceVariant,
          },
          style,
        ]}
      >
        <MaterialCommunityIcons
          name="credit-card-outline"
          size={size === 'tiny' ? 14 : size === 'small' ? 20 : size === 'medium' ? 32 : 48}
          color={theme.colors.onSurfaceVariant}
        />
      </View>
    );
  }

  return (
    <Image
      source={source}
      style={[
        size === 'large'
          ? { width: '100%', aspectRatio: CARD_ASPECT_RATIO }
          : { width: dimensions.width, height: dimensions.height },
        styles.image,
        style,
      ]}
      contentFit="contain"
      transition={200}
    />
  );
};

const styles = StyleSheet.create({
  placeholder: {
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  image: {
    borderRadius: 8,
  },
});

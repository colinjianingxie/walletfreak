import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Image } from 'expo-image';
import { useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { getPersonalityImage } from '../../utils/images';

interface PersonalityAvatarProps {
  slug: string;
  size?: number;
  style?: any;
}

export const PersonalityAvatar: React.FC<PersonalityAvatarProps> = ({
  slug,
  size = 48,
  style,
}) => {
  const theme = useTheme();
  const source = getPersonalityImage(slug);

  if (!source) {
    return (
      <View
        style={[
          styles.placeholder,
          {
            width: size,
            height: size,
            borderRadius: size / 2,
            backgroundColor: theme.colors.primaryContainer,
          },
          style,
        ]}
      >
        <MaterialCommunityIcons
          name="account-outline"
          size={size * 0.5}
          color={theme.colors.onPrimaryContainer}
        />
      </View>
    );
  }

  return (
    <Image
      source={source}
      style={[
        {
          width: size,
          height: size,
          borderRadius: size / 2,
        },
        style,
      ]}
      contentFit="cover"
      transition={200}
    />
  );
};

const styles = StyleSheet.create({
  placeholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
});

import React from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';

type ToolIconName = React.ComponentProps<typeof MaterialCommunityIcons>['name'];

const tools = [
  {
    id: 'worth-it',
    title: 'Worth It?',
    description: 'Calculate if your card is worth the annual fee',
    icon: 'scale-balance' as ToolIconName,
    route: '/stacks/worth-it-list',
  },
  {
    id: 'spend-optimizer',
    title: 'Spend Optimizer',
    description: 'Find the best card for each spending category',
    icon: 'chart-donut' as ToolIconName,
    route: '/stacks/spend-optimizer',
    premium: true,
  },
  {
    id: 'booking-optimizer',
    title: 'Booking Optimizer',
    description: 'Compare hotel bookings with cash vs points',
    icon: 'bed-outline' as ToolIconName,
    route: '/stacks/booking-optimizer',
    premium: true,
  },
  {
    id: 'award-scout',
    title: 'Award Scout',
    description: 'Find award availability for hotel stays',
    icon: 'magnify' as ToolIconName,
    route: '/stacks/award-scout',
    premium: true,
  },
  {
    id: 'points',
    title: 'Points Collection',
    description: 'Track your loyalty program balances',
    icon: 'star-circle-outline' as ToolIconName,
    route: '/stacks/points-collection',
  },
];

export default function ToolsScreen() {
  const router = useRouter();
  const theme = useTheme();

  return (
    <ScreenContainer>
      <View style={styles.grid}>
        {tools.map((tool) => (
          <Surface
            key={tool.id}
            style={[styles.toolCard, { backgroundColor: theme.colors.elevation.level1 }]}
            elevation={1}
          >
            <Pressable
              onPress={() => router.push(tool.route as any)}
              style={styles.toolPressable}
            >
              <MaterialCommunityIcons
                name={tool.icon}
                size={32}
                color={theme.colors.primary}
              />
              <Text variant="titleSmall" style={styles.toolTitle}>
                {tool.title}
              </Text>
              <Text
                variant="bodySmall"
                style={{ color: theme.colors.onSurfaceVariant }}
                numberOfLines={2}
              >
                {tool.description}
              </Text>
              {tool.premium && (
                <View style={[styles.premiumBadge, { backgroundColor: theme.colors.tertiaryContainer }]}>
                  <Text variant="labelSmall" style={{ color: theme.colors.onTertiaryContainer }}>
                    Premium
                  </Text>
                </View>
              )}
            </Pressable>
          </Surface>
        ))}
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  toolCard: {
    borderRadius: 16,
    width: '47%',
    flexGrow: 1,
  },
  toolPressable: {
    padding: 16,
    minHeight: 140,
  },
  toolTitle: {
    marginTop: 12,
    marginBottom: 4,
    fontFamily: 'Outfit-Medium',
  },
  premiumBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    marginTop: 8,
  },
});

import React from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Surface, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { formatRelativeTime } from '../../utils/formatters';

interface DatapointCardProps {
  datapoint: any;
  onVote: (id: string) => void;
}

export const DatapointCard: React.FC<DatapointCardProps> = ({ datapoint, onVote }) => {
  const theme = useTheme();

  return (
    <Surface style={[styles.container, { backgroundColor: theme.colors.elevation.level1 }]} elevation={1}>
      <View style={styles.content}>
        <View style={{ flex: 1 }}>
          <Text variant="titleSmall" numberOfLines={2}>
            {datapoint.benefit}
          </Text>
          <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 2 }}>
            {datapoint.card_name || datapoint.card_id}
          </Text>
          {datapoint.data && (
            <Text variant="bodySmall" style={{ marginTop: 4 }} numberOfLines={3}>
              {datapoint.data}
            </Text>
          )}
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 4 }}>
            {datapoint.author_name} · {formatRelativeTime(datapoint.created_at)}
          </Text>
        </View>
        <Pressable onPress={() => onVote(datapoint.id)} style={styles.voteButton}>
          <MaterialCommunityIcons
            name={datapoint.user_voted ? 'arrow-up-bold' : 'arrow-up-bold-outline'}
            size={22}
            color={datapoint.user_voted ? theme.colors.primary : theme.colors.onSurfaceVariant}
          />
          <Text
            variant="labelMedium"
            style={{ color: datapoint.user_voted ? theme.colors.primary : theme.colors.onSurfaceVariant }}
          >
            {datapoint.upvotes ?? 0}
          </Text>
        </Pressable>
      </View>
    </Surface>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    marginBottom: 8,
  },
  content: {
    flexDirection: 'row',
    padding: 16,
  },
  voteButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingLeft: 12,
  },
});

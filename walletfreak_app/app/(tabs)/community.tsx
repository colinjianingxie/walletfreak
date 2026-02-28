import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, SegmentedButtons, useTheme } from 'react-native-paper';
import { ScreenContainer } from '../../src/components/layout/ScreenContainer';
import { EmptyState } from '../../src/components/layout/EmptyState';

export default function CommunityScreen() {
  const [segment, setSegment] = useState('blog');
  const theme = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <SegmentedButtons
        value={segment}
        onValueChange={setSegment}
        buttons={[
          { value: 'blog', label: 'Blog' },
          { value: 'datapoints', label: 'Data Points' },
        ]}
        style={styles.segments}
      />

      {segment === 'blog' ? (
        <EmptyState
          icon="post-outline"
          title="Blog Posts"
          message="Community blog posts will appear here."
        />
      ) : (
        <EmptyState
          icon="chart-bubble"
          title="Data Points"
          message="Community data points will appear here."
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  segments: {
    marginBottom: 16,
  },
});

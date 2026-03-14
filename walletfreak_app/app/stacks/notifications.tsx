import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { Text, Switch, Button, Divider, useTheme } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useProfile, useUpdateNotifications } from '../../src/hooks/useProfile';
import { LoadingState } from '../../src/components/layout/LoadingState';

const BENEFIT_START_OPTIONS = [
  { label: '1 day before', value: 1 },
  { label: '3 days before', value: 3 },
  { label: '5 days before', value: 5 },
  { label: '7 days before', value: 7 },
  { label: '14 days before', value: 14 },
  { label: '30 days before', value: 30 },
];

const BENEFIT_REPEAT_OPTIONS = [
  { label: 'Daily', value: 1 },
  { label: 'Every 2 days', value: 2 },
  { label: 'Every 3 days', value: 3 },
  { label: 'Weekly', value: 7 },
];

const FEE_START_OPTIONS = [
  { label: '7 days before', value: 7 },
  { label: '14 days before', value: 14 },
  { label: '30 days before', value: 30 },
  { label: '45 days before', value: 45 },
  { label: '60 days before', value: 60 },
];

export default function NotificationsScreen() {
  const theme = useTheme();
  const { data: profile, isLoading } = useProfile();
  const updateNotifications = useUpdateNotifications();

  const [blogUpdates, setBlogUpdates] = useState(false);
  const [benefitEnabled, setBenefitEnabled] = useState(true);
  const [benefitStartDays, setBenefitStartDays] = useState(7);
  const [benefitRepeat, setBenefitRepeat] = useState(1);
  const [feeEnabled, setFeeEnabled] = useState(true);
  const [feeStartDays, setFeeStartDays] = useState(30);

  useEffect(() => {
    if (profile?.notification_preferences) {
      const prefs = profile.notification_preferences;
      setBlogUpdates(prefs.blog_updates?.enabled ?? false);
      setBenefitEnabled(prefs.benefit_expiration?.enabled ?? true);
      setBenefitStartDays(prefs.benefit_expiration?.start_days_before ?? 7);
      setBenefitRepeat(prefs.benefit_expiration?.repeat_frequency ?? 1);
      setFeeEnabled(prefs.annual_fee?.enabled ?? true);
      setFeeStartDays(prefs.annual_fee?.start_days_before ?? 30);
    }
  }, [profile]);

  const handleSave = () => {
    updateNotifications.mutate(
      {
        benefit_expiration: {
          enabled: benefitEnabled,
          start_days_before: benefitStartDays,
          repeat_frequency: benefitRepeat,
        },
        annual_fee: {
          enabled: feeEnabled,
          start_days_before: feeStartDays,
        },
        blog_updates: {
          enabled: blogUpdates,
        },
      },
      { onSuccess: () => Alert.alert('Saved', 'Notification preferences updated.') }
    );
  };

  if (isLoading) {
    return <LoadingState message="Loading..." />;
  }

  const getLabel = (options: { label: string; value: number }[], value: number) => {
    return options.find((o) => o.value === value)?.label || String(value);
  };

  const cycleOption = (
    options: { label: string; value: number }[],
    current: number,
    setter: (v: number) => void
  ) => {
    const idx = options.findIndex((o) => o.value === current);
    const next = (idx + 1) % options.length;
    setter(options[next].value);
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      {/* Blog Updates */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <MaterialCommunityIcons name="newspaper-variant-outline" size={20} color={theme.colors.primary} />
          <Text variant="titleSmall" style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>
            Blog Updates
          </Text>
        </View>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}>
          Get notified when new blog posts are published.
        </Text>
        <View style={styles.switchRow}>
          <Text variant="bodyMedium">Email notifications</Text>
          <Switch value={blogUpdates} onValueChange={setBlogUpdates} />
        </View>
      </View>

      <Divider style={styles.divider} />

      {/* Benefit Expiration */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <MaterialCommunityIcons name="clock-alert-outline" size={20} color={theme.colors.primary} />
          <Text variant="titleSmall" style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>
            Benefit Expiration
          </Text>
        </View>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}>
          Reminders before your card benefits expire.
        </Text>
        <View style={styles.switchRow}>
          <Text variant="bodyMedium">Enable reminders</Text>
          <Switch value={benefitEnabled} onValueChange={setBenefitEnabled} />
        </View>
        {benefitEnabled && (
          <>
            <View style={styles.optionRow}>
              <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
                Start notifying
              </Text>
              <Button
                mode="outlined"
                compact
                onPress={() => cycleOption(BENEFIT_START_OPTIONS, benefitStartDays, setBenefitStartDays)}
                style={styles.optionButton}
                labelStyle={{ fontSize: 12 }}
              >
                {getLabel(BENEFIT_START_OPTIONS, benefitStartDays)}
              </Button>
            </View>
            <View style={styles.optionRow}>
              <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
                Repeat frequency
              </Text>
              <Button
                mode="outlined"
                compact
                onPress={() => cycleOption(BENEFIT_REPEAT_OPTIONS, benefitRepeat, setBenefitRepeat)}
                style={styles.optionButton}
                labelStyle={{ fontSize: 12 }}
              >
                {getLabel(BENEFIT_REPEAT_OPTIONS, benefitRepeat)}
              </Button>
            </View>
          </>
        )}
      </View>

      <Divider style={styles.divider} />

      {/* Annual Fee Reminders */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <MaterialCommunityIcons name="calendar-alert" size={20} color={theme.colors.primary} />
          <Text variant="titleSmall" style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>
            Annual Fee Reminders
          </Text>
        </View>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginBottom: 8 }}>
          Get reminded before annual fees are charged.
        </Text>
        <View style={styles.switchRow}>
          <Text variant="bodyMedium">Enable reminders</Text>
          <Switch value={feeEnabled} onValueChange={setFeeEnabled} />
        </View>
        {feeEnabled && (
          <View style={styles.optionRow}>
            <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
              Start notifying
            </Text>
            <Button
              mode="outlined"
              compact
              onPress={() => cycleOption(FEE_START_OPTIONS, feeStartDays, setFeeStartDays)}
              style={styles.optionButton}
              labelStyle={{ fontSize: 12 }}
            >
              {getLabel(FEE_START_OPTIONS, feeStartDays)}
            </Button>
          </View>
        )}
      </View>

      <Button
        mode="contained"
        onPress={handleSave}
        loading={updateNotifications.isPending}
        style={styles.saveButton}
        labelStyle={{ fontFamily: 'Outfit-Medium' }}
      >
        Save Preferences
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  section: {
    marginBottom: 4,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  sectionTitle: {
    fontFamily: 'Outfit-SemiBold',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  optionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingLeft: 4,
  },
  optionButton: {
    borderRadius: 8,
  },
  divider: {
    marginVertical: 16,
  },
  saveButton: {
    borderRadius: 12,
    marginTop: 24,
  },
});

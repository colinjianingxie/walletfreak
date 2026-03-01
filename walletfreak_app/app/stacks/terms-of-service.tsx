import React from 'react';
import { ScrollView, View, StyleSheet, Linking } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

export default function TermsOfServiceScreen() {
  const theme = useTheme();

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      <Text style={styles.title}>Terms of Service</Text>
      <Text style={[styles.lastUpdated, { color: theme.colors.onSurfaceVariant }]}>
        Last Updated: January 3, 2026
      </Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>1. Introduction</Text>
        <Text style={styles.body}>
          Welcome to Wallet Freak ("Wallet Freak," "we," "our," or "us"). By accessing or using walletfreak.com and any related services (the "Service"), you agree to be bound by these Terms of Service and all applicable laws and regulations. If you do not agree with these terms, you may not use our Service.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>2. Eligibility and Accounts</Text>
        <Text style={styles.body}>
          You must be at least 13 years old to use Wallet Freak. When creating an account, you agree to provide accurate and complete information and to keep your account credentials secure. You are responsible for all activity that occurs under your account.
        </Text>
        <Text style={styles.body}>
          We reserve the right to suspend or terminate accounts that violate these Terms.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>3. Use License</Text>
        <Text style={styles.body}>
          Permission is granted to temporarily access and use Wallet Freak's materials and services for personal, non-commercial use only. This is a license, not a transfer of title. Under this license, you may not:
        </Text>
        <Text style={styles.bullet}>{'\u2022'} Modify, copy, or redistribute the materials</Text>
        <Text style={styles.bullet}>{'\u2022'} Use the materials for any commercial purpose or public display</Text>
        <Text style={styles.bullet}>{'\u2022'} Attempt to decompile, reverse engineer, or interfere with any software or systems</Text>
        <Text style={styles.bullet}>{'\u2022'} Remove copyright or proprietary notices</Text>
        <Text style={styles.bullet}>{'\u2022'} Mirror or host the materials on another server</Text>
        <Text style={styles.body}>
          This license automatically terminates if you violate these Terms.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>4. Financial Information Disclaimer</Text>
        <Text style={styles.body}>
          Wallet Freak provides educational and informational content only. We do not provide financial, investment, legal, or tax advice. Any insights, recommendations, or comparisons are general in nature and should not be relied upon as a substitute for professional advice.
        </Text>
        <Text style={styles.body}>
          You acknowledge that any financial decisions you make are solely your responsibility.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>5. Accuracy of Information</Text>
        <Text style={styles.body}>
          While we strive to keep information accurate and up to date, Wallet Freak does not warrant that all content is complete, current, or error-free. Credit card benefits, fees, and offers may change at any time without notice.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>6. Disclaimer of Warranties</Text>
        <Text style={styles.body}>
          The Service and materials are provided on an "as is" and "as available" basis. Wallet Freak disclaims all warranties, express or implied, including but not limited to implied warranties of merchantability, fitness for a particular purpose, and non-infringement.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>7. Limitation of Liability</Text>
        <Text style={styles.body}>
          To the fullest extent permitted by law, Wallet Freak and its suppliers shall not be liable for any indirect, incidental, special, or consequential damages, including loss of data, profits, or business interruption, arising out of the use or inability to use the Service — even if advised of the possibility of such damages.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>8. Termination</Text>
        <Text style={styles.body}>
          We may suspend or terminate access to the Service at any time, without prior notice, for conduct that we believe violates these Terms or is harmful to other users or to Wallet Freak.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>9. Changes to These Terms</Text>
        <Text style={styles.body}>
          We may revise these Terms of Service at any time. Updated terms will be posted on this page with a revised "Last Updated" date. Continued use of the Service constitutes acceptance of the updated terms.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>10. Governing Law</Text>
        <Text style={styles.body}>
          These Terms are governed by and construed in accordance with the laws of the United States, without regard to conflict of law principles.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>11. Contact Us</Text>
        <Text style={styles.body}>
          If you have any questions about these Terms of Service, please contact us at:
        </Text>
        <Text
          style={[styles.link, { color: theme.colors.primary }]}
          onPress={() => Linking.openURL('mailto:colin@walletfreak.com')}
        >
          colin@walletfreak.com
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 20,
    paddingBottom: 48,
  },
  title: {
    fontSize: 28,
    fontFamily: 'Outfit-Bold',
    color: '#1C1B1F',
    marginBottom: 4,
  },
  lastUpdated: {
    fontSize: 14,
    fontFamily: 'Outfit',
    marginBottom: 28,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontFamily: 'Outfit-SemiBold',
    color: '#1C1B1F',
    marginBottom: 10,
  },
  body: {
    fontSize: 15,
    fontFamily: 'Outfit',
    color: '#49454F',
    lineHeight: 22,
    marginBottom: 8,
  },
  bullet: {
    fontSize: 15,
    fontFamily: 'Outfit',
    color: '#49454F',
    lineHeight: 22,
    paddingLeft: 16,
    marginBottom: 4,
  },
  link: {
    fontSize: 15,
    fontFamily: 'Outfit-Medium',
    textDecorationLine: 'underline',
  },
});

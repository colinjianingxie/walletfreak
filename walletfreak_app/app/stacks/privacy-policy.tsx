import React from 'react';
import { ScrollView, View, StyleSheet, Linking } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

export default function PrivacyPolicyScreen() {
  const theme = useTheme();

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      <Text style={styles.title}>Privacy Policy</Text>
      <Text style={[styles.lastUpdated, { color: theme.colors.onSurfaceVariant }]}>
        Last Updated: January 3, 2026
      </Text>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>1. Introduction</Text>
        <Text style={styles.body}>
          Welcome to Wallet Freak ("we," "our," or "us"). We respect your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit walletfreak.com or use our services.
        </Text>
        <Text style={styles.body}>
          By using our website, you agree to the collection and use of information in accordance with this policy.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>2. Data We Collect</Text>
        <Text style={styles.body}>
          We may collect, use, store, and transfer the following categories of personal data:
        </Text>
        <Text style={styles.bullet}>{'\u2022'} Identity Data: first name, last name, username, or similar identifier</Text>
        <Text style={styles.bullet}>{'\u2022'} Contact Data: email address</Text>
        <Text style={styles.bullet}>{'\u2022'} Technical Data: IP address, browser type and version, device information, operating system, time zone, and other technical identifiers</Text>
        <Text style={styles.bullet}>{'\u2022'} Usage Data: information about how you interact with our website and services</Text>
        <Text style={styles.body}>
          We do not knowingly collect sensitive personal data.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>3. How We Use Your Data</Text>
        <Text style={styles.body}>
          We use your personal data only where permitted by law, including:
        </Text>
        <Text style={styles.bullet}>{'\u2022'} To provide and maintain our services</Text>
        <Text style={styles.bullet}>{'\u2022'} To manage user accounts and authentication</Text>
        <Text style={styles.bullet}>{'\u2022'} To improve website performance and user experience</Text>
        <Text style={styles.bullet}>{'\u2022'} To communicate with you regarding service-related matters</Text>
        <Text style={styles.bullet}>{'\u2022'} To comply with legal or regulatory obligations</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>4. Cookies and Analytics</Text>
        <Text style={styles.body}>
          We may use cookies and similar technologies to understand how users interact with our website. These tools help us analyze usage patterns and improve functionality. You can control cookie preferences through your browser settings.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>5. Third-Party Services</Text>
        <Text style={styles.body}>
          We may use trusted third-party service providers to operate our website and services, including authentication, hosting, and analytics providers. These third parties process data only on our instructions and are subject to appropriate confidentiality and security obligations.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>6. Data Security</Text>
        <Text style={styles.body}>
          We implement reasonable technical and organizational safeguards to protect your personal data against unauthorized access, loss, misuse, or disclosure. Access to personal data is limited to those with a legitimate business need.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>7. Data Retention</Text>
        <Text style={styles.body}>
          We retain personal data only for as long as necessary to fulfill the purposes outlined in this policy, unless a longer retention period is required or permitted by law.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>8. Your Privacy Rights</Text>
        <Text style={styles.body}>
          Depending on your location, you may have rights to:
        </Text>
        <Text style={styles.bullet}>{'\u2022'} Access your personal data</Text>
        <Text style={styles.bullet}>{'\u2022'} Request correction or deletion of your data</Text>
        <Text style={styles.bullet}>{'\u2022'} Object to or restrict certain processing</Text>
        <Text style={styles.body}>
          To exercise these rights, please contact us using the details below.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>9. Children's Privacy</Text>
        <Text style={styles.body}>
          Wallet Freak is not intended for use by individuals under the age of 13. We do not knowingly collect personal data from children.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>10. Changes to This Policy</Text>
        <Text style={styles.body}>
          We may update this Privacy Policy from time to time. Any changes will be posted on this page with an updated revision date.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>11. Contact Us</Text>
        <Text style={styles.body}>
          If you have any questions about this Privacy Policy or our privacy practices, please contact us at:
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

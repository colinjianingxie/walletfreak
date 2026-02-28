import { Link, Stack } from 'expo-router';
import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';

export default function NotFoundScreen() {
  return (
    <>
      <Stack.Screen options={{ title: 'Not Found' }} />
      <View style={styles.container}>
        <Text variant="headlineMedium">Page not found</Text>
        <Link href="/" style={styles.link}>
          <Text variant="bodyLarge" style={styles.linkText}>
            Go to home screen
          </Text>
        </Link>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  link: {
    marginTop: 16,
  },
  linkText: {
    color: '#6750A4',
  },
});

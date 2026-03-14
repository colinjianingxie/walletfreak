import React from 'react';
import { View, StyleSheet, Image, Pressable } from 'react-native';
import { Text, Checkbox } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { PriceLevelBadge } from './PriceLevelBadge';
import type { HotelSearchResult } from '../../types/booking';

interface HotelCardProps {
  hotel: HotelSearchResult;
  selected: boolean;
  onToggle: () => void;
}

const BRAND_COLORS: Record<string, string> = {
  hyatt: '#1E3A5F',
  hilton: '#003B5C',
  marriott: '#B91C1C',
  ihg: '#006633',
  independent: '#6B7280',
};

export const HotelCard: React.FC<HotelCardProps> = ({ hotel, selected, onToggle }) => {
  const brandColor = BRAND_COLORS[hotel.brand_class] || BRAND_COLORS.independent;

  return (
    <Pressable
      onPress={onToggle}
      style={[styles.card, selected && styles.cardSelected]}
    >
      {/* Brand color bar */}
      <View style={[styles.brandBar, { backgroundColor: brandColor }]} />

      {/* Photo */}
      {hotel.photo_url ? (
        <Image source={{ uri: hotel.photo_url }} style={styles.photo} />
      ) : (
        <View style={[styles.photo, styles.photoPlaceholder]}>
          <MaterialCommunityIcons name="image-off-outline" size={24} color="#CBD5E1" />
        </View>
      )}

      {/* Content */}
      <View style={styles.content}>
        <View style={styles.headerRow}>
          <Text style={styles.name} numberOfLines={2}>
            {hotel.name}
          </Text>
          <Checkbox
            status={selected ? 'checked' : 'unchecked'}
            onPress={onToggle}
          />
        </View>

        {/* Rating */}
        <View style={styles.ratingRow}>
          <MaterialCommunityIcons name="star" size={14} color="#FACC15" />
          <Text style={styles.ratingText}>{hotel.rating.toFixed(1)}</Text>
          <Text style={styles.reviewCount}>
            ({hotel.user_rating_count.toLocaleString()})
          </Text>
          {hotel.rate_per_night == null && hotel.price_level > 0 && (
            <PriceLevelBadge level={hotel.price_level} />
          )}
        </View>

        {/* Price */}
        {hotel.rate_per_night != null && (
          <View>
            <View style={styles.priceRow}>
              <Text style={styles.priceText}>${Math.round(hotel.rate_per_night)}</Text>
              <Text style={styles.priceNight}> / night</Text>
            </View>
            {hotel.price_history && hotel.price_history.prior_avg !== hotel.rate_per_night && (
              <View style={styles.priceTrendRow}>
                <MaterialCommunityIcons
                  name={hotel.rate_per_night > hotel.price_history.prior_avg ? 'trending-up' : 'trending-down'}
                  size={12}
                  color={hotel.rate_per_night > hotel.price_history.prior_avg ? '#EF4444' : '#22C55E'}
                />
                <Text style={[
                  styles.priceTrendText,
                  { color: hotel.rate_per_night > hotel.price_history.prior_avg ? '#EF4444' : '#22C55E' },
                ]}>
                  was ${Math.round(hotel.price_history.prior_avg)} avg
                </Text>
              </View>
            )}
            {hotel.is_cached && (
              <View style={styles.cachedBadge}>
                <Text style={styles.cachedText}>CACHED</Text>
              </View>
            )}
          </View>
        )}

        {/* Brand + Address */}
        <Text style={styles.brand}>{hotel.brand}</Text>
        <Text style={styles.address} numberOfLines={1}>
          {hotel.address}
        </Text>
        {hotel.program_name ? (
          <View style={styles.programBadge}>
            <MaterialCommunityIcons name="card-account-details-outline" size={10} color="#6366F1" />
            <Text style={styles.programText}>{hotel.program_name}</Text>
          </View>
        ) : null}

        {/* Premium Program Badges */}
        {(hotel.premium_programs?.amex_fhr || hotel.premium_programs?.amex_thc || hotel.premium_programs?.chase_edit) && (
          <View style={styles.premiumRow}>
            {hotel.premium_programs.amex_fhr && (
              <View style={styles.fhrBadge}>
                <MaterialCommunityIcons name="diamond-stone" size={10} color="#C9B037" />
                <Text style={styles.fhrText}>FHR</Text>
              </View>
            )}
            {hotel.premium_programs.amex_thc && (
              <View style={styles.thcBadge}>
                <MaterialCommunityIcons name="star-outline" size={10} color="#94A3B8" />
                <Text style={styles.thcText}>THC</Text>
              </View>
            )}
            {hotel.premium_programs.chase_edit && (
              <View style={styles.editBadge}>
                <MaterialCommunityIcons name="bookmark-check" size={10} color="#FFFFFF" />
                <Text style={styles.editText}>
                  The Edit{hotel.premium_programs.chase_edit.chase_2026_credit ? ' +$' : ''}
                </Text>
              </View>
            )}
          </View>
        )}
      </View>
    </Pressable>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    overflow: 'hidden',
    marginBottom: 12,
  },
  cardSelected: {
    borderColor: '#6366F1',
    borderWidth: 2,
  },
  brandBar: {
    height: 4,
  },
  photo: {
    width: '100%',
    height: 140,
    backgroundColor: '#F1F5F9',
  },
  photoPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: 12,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  name: {
    fontSize: 15,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
    flex: 1,
    marginRight: 8,
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  ratingText: {
    fontSize: 13,
    fontFamily: 'Outfit-SemiBold',
    color: '#0F172A',
  },
  reviewCount: {
    fontSize: 11,
    fontFamily: 'Outfit',
    color: '#94A3B8',
    marginRight: 6,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginTop: 6,
  },
  priceText: {
    fontSize: 18,
    fontFamily: 'Outfit-Bold',
    color: '#0F172A',
  },
  priceNight: {
    fontSize: 12,
    fontFamily: 'Outfit',
    color: '#94A3B8',
  },
  priceTrendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    marginTop: 2,
  },
  priceTrendText: {
    fontSize: 10,
    fontFamily: 'Outfit-SemiBold',
  },
  cachedBadge: {
    backgroundColor: '#F1F5F9',
    borderRadius: 4,
    paddingHorizontal: 5,
    paddingVertical: 1,
    alignSelf: 'flex-start',
    marginTop: 3,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  cachedText: {
    fontSize: 9,
    fontFamily: 'Outfit-SemiBold',
    color: '#94A3B8',
    letterSpacing: 0.3,
  },
  brand: {
    fontSize: 12,
    fontFamily: 'Outfit-Medium',
    color: '#64748B',
    marginTop: 6,
  },
  address: {
    fontSize: 11,
    fontFamily: 'Outfit',
    color: '#94A3B8',
    marginTop: 2,
  },
  programBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  programText: {
    fontSize: 10,
    fontFamily: 'Outfit-Medium',
    color: '#6366F1',
  },
  premiumRow: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 6,
    flexWrap: 'wrap',
  },
  fhrBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#1A1A2E',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 99,
    borderWidth: 1,
    borderColor: '#C9B037',
  },
  fhrText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    color: '#C9B037',
  },
  thcBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#1E293B',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 99,
    borderWidth: 1,
    borderColor: '#475569',
  },
  thcText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    color: '#94A3B8',
  },
  editBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    backgroundColor: '#003087',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 99,
    borderWidth: 1,
    borderColor: '#2563EB',
  },
  editText: {
    fontSize: 10,
    fontFamily: 'Outfit-Bold',
    color: '#FFFFFF',
  },
});

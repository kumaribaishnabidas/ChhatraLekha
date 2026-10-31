import SwiftUI

/// Accessible card presenting a metric or status indicator with an icon.
public struct StatCard: View {
    public let title: String
    public let value: String
    public let subtitle: String?
    public let iconName: String
    public let iconColor: Color

    public init(
        title: String,
        value: String,
        subtitle: String? = nil,
        iconName: String,
        iconColor: Color = .brandPrimary
    ) {
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.iconName = iconName
        self.iconColor = iconColor
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(title)
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundColor(.inkMuted)
                    .textCase(.uppercase)
                Spacer()
                Image(systemName: iconName)
                    .font(.subheadline)
                    .foregroundColor(iconColor)
            }
            Text(value)
                .font(.title2)
                .fontWeight(.heavy)
                .foregroundColor(.inkPrimary)
            if let sub = subtitle {
                Text(sub)
                    .font(.caption2)
                    .foregroundColor(.inkMuted)
            }
        }
        .padding(14)
        .background(Color.surfaceBackground)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color.borderLine, lineWidth: 1)
        )
    }
}


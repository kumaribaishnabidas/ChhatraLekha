import SwiftUI

/// Accessible empty state placeholder.
public struct EmptyStateView: View {
    public let title: String
    public let message: String
    public let iconName: String
    public let actionTitle: String?
    public let action: (() -> Void)?

    public init(
        title: String,
        message: String,
        iconName: String = "tray",
        actionTitle: String? = nil,
        action: (() -> Void)? = nil
    ) {
        self.title = title
        self.message = message
        self.iconName = iconName
        self.actionTitle = actionTitle
        self.action = action
    }

    public var body: some View {
        VStack(spacing: 12) {
            Image(systemName: iconName)
                .font(.system(size: 44, weight: .light))
                .foregroundColor(.inkMuted)
                .padding(.bottom, 4)
            Text(title)
                .font(.headline)
                .foregroundColor(.inkPrimary)
            Text(message)
                .font(.subheadline)
                .foregroundColor(.inkMuted)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            if let actTitle = actionTitle, let act = action {
                Button(action: act) {
                    Text(actTitle)
                        .font(.subheadline.bold())
                        .foregroundColor(.brandPrimary)
                }
                .padding(.top, 8)
            }
        }
        .padding(32)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

/// Accessible error state presentation with retry mechanism.
public struct ErrorStateView: View {
    public let message: String
    public let onRetry: () -> Void

    public init(message: String, onRetry: @escaping () -> Void) {
        self.message = message
        self.onRetry = onRetry
    }

    public var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 40))
                .foregroundColor(.errorCrimson)
            Text("Operation Encountered an Issue")
                .font(.headline)
            Text(message)
                .font(.subheadline)
                .foregroundColor(.inkMuted)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
            Button(action: onRetry) {
                HStack(spacing: 6) {
                    Image(systemName: "arrow.clockwise")
                    Text("Try Again")
                }
                .font(.subheadline.bold())
                .foregroundColor(.brandPrimary)
            }
            .padding(.top, 8)
        }
        .padding(24)
        .frame(maxWidth: .infinity)
    }
}

